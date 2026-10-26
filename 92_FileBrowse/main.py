"""共有フォルダのファイルを ダウンロード / アップロード / 削除 するだけの簡易Webアプリ（サブフォルダ・複数共有対応）。

環境変数:
  SHARES     公開する共有の一覧。「名前=フォルダ」を ; で区切る
             例: PCOM=D:\\Kanri\\fit_order;XXXX=D:\\別のフォルダ → http://IP/PCOM/ と http://IP/XXXX/
             （未設定のときは下の FILES_DIR / BASE_PATH の1共有だけで動く）
  FILES_DIR  SHARES 未設定時の対象フォルダ（既定: ./files）
  BASE_PATH  SHARES 未設定時の公開パス（既定: 空=ルート。例: /PCOM）
  MAX_MB     アップロード上限MB（既定: 0=無制限）
  TRASH_DAYS 削除したファイル・フォルダを .trash に残す日数（既定: 30。0=自動削除しない）
"""

import os
import re
import shutil
import tempfile
import threading
import time
import zipfile
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
MAX_BYTES = int(os.environ.get("MAX_MB", "0")) * 1024 * 1024
TRASH_DAYS = int(os.environ.get("TRASH_DAYS", "30"))
CHUNK = 1024 * 1024

SHARE_NAME = re.compile(r"^[\w.-]+$")


def load_shares() -> dict[str, Path]:
    """公開する共有を {URLの名前: 実フォルダ} で返す。名前が空文字の共有はルート（/）で公開する。"""
    raw = os.environ.get("SHARES", "").strip()
    if not raw:  # 単一フォルダ（従来の設定）
        folder = Path(os.environ.get("FILES_DIR", BASE_DIR / "files")).resolve()
        folder.mkdir(parents=True, exist_ok=True)
        return {os.environ.get("BASE_PATH", "").strip("/"): folder}

    shares: dict[str, Path] = {}
    for entry in filter(None, (e.strip() for e in raw.split(";"))):
        name, _, folder = entry.partition("=")
        name, folder = name.strip().strip("/"), folder.strip()
        if not SHARE_NAME.match(name) or not folder:
            raise SystemExit(f"SHARES の書式が正しくありません（名前=フォルダ）: {entry}")
        if name.lower() in {n.lower() for n in shares}:
            raise SystemExit(f"SHARES の名前が重複しています（大文字小文字は区別されません）: {name}")
        path = Path(folder).resolve()
        if not path.is_dir():  # 打ち間違いで見当違いのフォルダを作らないよう、無ければ起動しない
            raise SystemExit(f"フォルダが存在しません: {name} → {path}")
        shares[name] = path
    return shares


SHARES = load_shares()

# 共有ごとのヘッダー色（SHARES に書いた順に割り当てる。白文字が読める落ち着いた色）
HEADER_COLORS = ["#3f6f73", "#46607f", "#7b6a4d", "#6a5a7c", "#59704d", "#85595f"]


def purge_trash(root: Path):
    """.trash 内の、削除から TRASH_DAYS 日を過ぎたファイル・フォルダを消す（削除時に更新日時を現在時刻にしてある）。"""
    trash = root / ".trash"
    if not TRASH_DAYS or not trash.is_dir():
        return
    limit = time.time() - TRASH_DAYS * 86400
    for p in trash.iterdir():
        try:
            if p.stat().st_mtime >= limit:
                continue
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
        except OSError:
            pass  # 使用中など。次回の実行で再試行する


def purge_loop():
    while True:
        for root in SHARES.values():
            purge_trash(root)
        time.sleep(24 * 3600)


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=purge_loop, daemon=True).start()
    yield


# 末尾スラッシュ補完（redirect_slashes）はHostヘッダーから絶対URLを作るため、IISのリバースプロキシ越しだと
# 127.0.0.1:3000 に飛んでしまう。無効にして、/名前 → /名前/ は下で自前で補う
app = FastAPI(title="FileBrowse", redoc_url=None, lifespan=lifespan)
app.router.redirect_slashes = False


class CaseInsensitiveShare:
    """/pcom/ でも /PCOM/ として扱う（IISは大文字小文字を区別しないので、直接アクセスでも揃える）。"""

    def __init__(self, asgi_app):
        self.app = asgi_app
        self.canonical = {n.lower(): n for n in SHARES if n}

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            first, sep, rest = scope["path"][1:].partition("/")
            canon = self.canonical.get(first.lower())
            if canon and canon != first:
                scope = {**scope, "path": f"/{canon}{sep}{rest}"}
        await self.app(scope, receive, send)


app.add_middleware(CaseInsensitiveShare)

# Windowsで使えない文字・予約名・末尾のドット/空白
INVALID_NAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]|[. ]$|^(CON|PRN|AUX|NUL|COM\d|LPT\d)(\..*)?$', re.I)


def check_name(name: str):
    """ファイル名・フォルダ名1つ分の検証。"." 始まり（.trash や一時ファイル）も不可。"""
    if not name or name.startswith(".") or INVALID_NAME.search(name):
        raise HTTPException(400, "使用できない名前です")


class Paths(BaseModel):
    paths: list[str]


class MovePaths(Paths):
    dest: str = ""


class ZipSink:
    """ZipFile の出力先。書かれたバイト列を溜めて呼び出し側が取り出して流す（一時ファイルを作らない）。"""

    def __init__(self):
        self.buf = bytearray()
        self.pos = 0

    def write(self, data):
        self.buf += data
        self.pos += len(data)
        return len(data)

    def tell(self):
        return self.pos

    def flush(self):
        pass

    def take(self):
        data = bytes(self.buf)
        self.buf.clear()
        return data


def zip_stream(folder: Path):
    """フォルダの中身をZIPにしながら送る。圧縮なし（大半がPDF/Office等で効果が薄く、速い）。"""
    sink = ZipSink()
    with zipfile.ZipFile(sink, "w", zipfile.ZIP_STORED) as zf:
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            rel_root = Path(root).relative_to(folder)
            if rel_root.parts:
                zf.writestr(zipfile.ZipInfo(rel_root.as_posix() + "/"), b"")  # 空フォルダも残す
            for name in files:
                if name.startswith("."):
                    continue
                src = Path(root) / name
                info = zipfile.ZipInfo.from_file(src, (rel_root / name).as_posix(), strict_timestamps=False)
                with open(src, "rb") as f, zf.open(info, "w") as dst:
                    while chunk := f.read(CHUNK):
                        dst.write(chunk)
                        yield sink.take()
    yield sink.take()  # 末尾（ZIPの終端情報。with を抜けた時点で書き込まれる）


def failure(path: str, e: Exception) -> dict:
    return {"path": path, "detail": e.detail if isinstance(e, HTTPException) else "操作できません（使用中の可能性があります）"}


def build_router(share: str, files_dir: Path, color: str) -> APIRouter:
    """1つの共有（フォルダ）ぶんのAPIと画面。共有ごとに files_dir と .trash が独立する。"""
    trash_dir = files_dir / ".trash"
    router = APIRouter(generate_unique_id_function=lambda r: f"{share}_{r.name}")

    def resolve_path(rel: str) -> Path:
        """"a/b/c.txt" 形式の相対パスを検証し、共有フォルダ配下の実パスを返す（パストラバーサル対策）。空文字は共有フォルダ自身。"""
        parts = [p for p in rel.split("/") if p]
        for p in parts:
            check_name(p)
        path = files_dir.joinpath(*parts).resolve()
        if path != files_dir and files_dir not in path.parents:  # シンボリックリンク等で外へ出るのも防ぐ
            raise HTTPException(400, "使用できないパスです")
        return path

    def resolve_dir(rel: str) -> Path:
        path = resolve_path(rel)
        if not path.is_dir():
            raise HTTPException(404, "フォルダが見つかりません")
        return path

    def existing_item(path: str) -> Path:
        """一括操作の対象1件を検証して返す。共有フォルダ自身と、存在しないものは不可。"""
        target = resolve_path(path)
        if target == files_dir:
            raise HTTPException(400, "対象フォルダ自身は操作できません")
        if not target.exists():
            raise HTTPException(404, "見つかりません")
        return target

    @router.get("/api/files")
    def list_files(path: str = ""):
        items = []
        for p in resolve_dir(path).iterdir():
            if p.name.startswith("."):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            if p.is_dir():
                items.append({"name": p.name, "type": "dir", "size": None, "modified": st.st_mtime})
            elif p.is_file():
                items.append({"name": p.name, "type": "file", "size": st.st_size, "modified": st.st_mtime})
        items.sort(key=lambda x: (x["type"] != "dir", x["name"].lower()))
        return items

    @router.get("/api/download")
    def download(path: str):
        target = resolve_path(path)
        if target.is_file():
            return FileResponse(target, filename=target.name)
        if target.is_dir() and target != files_dir:
            disposition = f"attachment; filename*=UTF-8''{quote(target.name + '.zip')}"
            return StreamingResponse(zip_stream(target), media_type="application/zip", headers={"Content-Disposition": disposition})
        raise HTTPException(404, "見つかりません")

    @router.post("/api/files")
    def upload_file(file: UploadFile, path: str = "", overwrite: bool = False):
        folder = resolve_dir(path)
        # ブラウザによってはフルパスで送られてくるので末尾だけ使う
        name = (file.filename or "").replace("\\", "/").split("/")[-1]
        check_name(name)
        dest = folder / name
        if dest.is_dir():
            raise HTTPException(400, "同名のフォルダが存在します")
        if dest.exists() and not overwrite:
            raise HTTPException(409, "同名のファイルが既に存在します")

        # 同じフォルダの一時ファイルへ書いてから置換する（途中で切れても本体を壊さない）
        fd, tmp = tempfile.mkstemp(prefix=".upload-", dir=folder)
        size = 0
        try:
            with os.fdopen(fd, "wb") as out:
                while chunk := file.file.read(CHUNK):
                    size += len(chunk)
                    if MAX_BYTES and size > MAX_BYTES:
                        raise HTTPException(413, f"ファイルサイズが上限（{MAX_BYTES // 1024 // 1024}MB）を超えています")
                    out.write(chunk)
            os.replace(tmp, dest)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        return {"name": dest.name, "size": size}

    @router.post("/api/folders")
    def create_folder(path: str = "", name: str = ""):
        parent = resolve_dir(path)
        check_name(name)
        new = parent / name
        if new.exists():
            raise HTTPException(409, "同名のファイルまたはフォルダが既に存在します")
        try:
            new.mkdir()
        except OSError:
            raise HTTPException(400, "フォルダを作成できません（パスが長すぎる可能性があります）")
        return {"name": name}

    @router.post("/api/delete")
    def delete_items(req: Paths):
        """削除は .trash へ退避する（誤削除の復旧用。TRASH_DAYS 日後に自動で完全削除される）。フォルダは中身ごと。
        1件ずつ処理し、失敗したものは理由つきで返す（成功したものは反映される）。"""
        done, errors = 0, []
        for p in req.paths:
            try:
                target = existing_item(p)
                trash_dir.mkdir(exist_ok=True)
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest = trash_dir / f"{stamp}_{target.name}"
                shutil.move(str(target), dest)
                os.utime(dest)  # 保持期間は「削除した日」から数える（moveは元の更新日時を保つため）
                done += 1
            except (HTTPException, OSError) as e:
                errors.append(failure(p, e))
        return {"done": done, "errors": errors}

    @router.post("/api/move")
    def move_items(req: MovePaths):
        """指定フォルダへ移動する。同名があれば移動しない（上書きしない）。"""
        dest_dir = resolve_dir(req.dest)
        done, errors = 0, []
        for p in req.paths:
            try:
                src = existing_item(p)
                if src.parent == dest_dir:
                    raise HTTPException(400, "既にそのフォルダにあります")
                if src.is_dir() and (src == dest_dir or src in dest_dir.parents):
                    raise HTTPException(400, "フォルダを自分自身の中へは移動できません")
                target = dest_dir / src.name
                if target.exists():
                    raise HTTPException(409, "移動先に同じ名前があります")
                shutil.move(str(src), target)
                done += 1
            except (HTTPException, OSError) as e:
                errors.append(failure(p, e))
        return {"done": done, "errors": errors}

    @router.get("/", include_in_schema=False)
    def index():
        # 画面の見出し等に、この共有の名前と色を埋め込む（名前は SHARE_NAME で検証済みなのでHTMLに入れて安全）
        html = (BASE_DIR / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(html.replace("__SHARE_NAME__", share or "ファイル共有").replace("__SHARE_COLOR__", color))

    return router


def slash_redirect(target: str):
    # 画面の相対パス（api/files）が解決できるよう末尾スラッシュ付きへ。Hostに依存しないパス指定で返す
    def handler():
        return RedirectResponse(target)

    return handler


for i, (name, folder) in enumerate(SHARES.items()):
    app.include_router(build_router(name, folder, HEADER_COLORS[i % len(HEADER_COLORS)]), prefix=f"/{name}" if name else "")
    if name:
        app.add_api_route(f"/{name}", slash_redirect(f"/{name}/"), methods=["GET"], include_in_schema=False)
