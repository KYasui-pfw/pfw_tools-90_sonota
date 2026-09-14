"""
C:\\Dev\\90_tools\\88_obl_oracle  →  esrv11:/home/docker-user/docker-apps/12_obl_oracle

コード類だけを一方向で同期する。手元がマスター。

使い方:
    $PYTHON deploy.py             # 差分を表示して転送
    $PYTHON deploy.py --dry-run   # 転送せず差分だけ表示

    $PYTHON = C:/Dev/90_tools/09_EJ_rBOM_マッピング２/venv/Scripts/python.exe

同期するもの:
    docker-compose.yml / refresh.sh / setup/*.sql

同期しないもの（esrv11 側にしか存在しない。転送すると壊れる）:
    .env          パスワード。Git にも載せない
    oradata/      DB本体（約11GB）
    dmp/          ダンプの展開先（約3GB）
    logs/         実行ログ
    .last_dmp_sig 前回取り込んだ dmp の識別子

注意:
    esrv11 側で直接編集しないこと。次の deploy で上書きされて消える。
"""

from __future__ import annotations

import hashlib
import os
import posixpath
import sys
from pathlib import Path

import paramiko

HOST = "esrv11"
USER = "docker-user"
PASSWORD = os.environ.get("ESRV11_PASSWORD", "duadmin")
REMOTE_ROOT = "/home/docker-user/docker-apps/12_obl_oracle"

LOCAL_ROOT = Path(__file__).resolve().parent

# 転送するファイル（相対パス）。増やすときはここに足す
SYNC_FILES = [
    "docker-compose.yml",
    "refresh.sh",
    "setup/01_init.sql",
]

# 実行権限を付けるもの
EXECUTABLE = {"refresh.sh"}


def to_lf(data: bytes) -> bytes:
    """Windows で編集した CRLF を LF に直す。bash も sqlplus も CR があると誤動作する。"""
    return data.replace(b"\r\n", b"\n")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def main() -> int:
    dry_run = "--dry-run" in sys.argv

    payloads: dict[str, bytes] = {}
    for rel in SYNC_FILES:
        p = LOCAL_ROOT / rel
        if not p.is_file():
            print(f"[NG] ローカルに存在しない: {rel}")
            return 1
        payloads[rel] = to_lf(p.read_bytes())

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=20)
    sftp = client.open_sftp()

    changed = 0
    for rel, data in payloads.items():
        remote = posixpath.join(REMOTE_ROOT, rel)

        # 既存の内容と比較して、変わっていないものは触らない
        try:
            with sftp.open(remote, "rb") as f:
                current = f.read()
        except IOError:
            current = None

        if current == data:
            print(f"     同じ    {rel}  ({sha(data)})")
            continue

        changed += 1
        state = "新規" if current is None else "更新"
        print(f"  -> {state}    {rel}  ({sha(current) if current else '-'} -> {sha(data)})")

        if dry_run:
            continue

        parent = posixpath.dirname(remote)
        try:
            sftp.stat(parent)
        except IOError:
            sftp.mkdir(parent)

        with sftp.open(remote, "wb") as f:
            f.write(data)
        sftp.chmod(remote, 0o755 if rel in EXECUTABLE else 0o644)

    sftp.close()
    client.close()

    if dry_run:
        print(f"\n--dry-run のため転送していません（差分 {changed} 件）")
    elif changed == 0:
        print("\n差分なし。転送は行いませんでした")
    else:
        print(f"\n{changed} 件を {HOST}:{REMOTE_ROOT} へ転送しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
