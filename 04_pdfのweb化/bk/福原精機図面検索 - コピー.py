import streamlit as st
import base64
import os
from pathlib import Path
import glob
import fitz  # PyMuPDF
from PIL import Image
import io
import json
import time
import asyncio
import concurrent.futures
from typing import Dict, List, Tuple

# --- 設定項目 ---
ROOT_DIR_PATH_STR = r"\\fsrv24\zumen"
PAGE_TITLE = "福原精機図面検索"
STRUCTURE_JSON_PATH = Path(__file__).parent / "folder_structure.json"
METADATA_JSON_PATH = Path(__file__).parent / "folder_metadata.json"
AUTO_UPDATE_INTERVAL = 300  # 5分 = 300秒

# --- Streamlit ページ設定 ---
st.set_page_config(page_title=PAGE_TITLE, layout="wide")

HIDE_ST_STYLE = """
        <style>
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        #MainMenu,
        header,
        footer {
            display: none !important; /* 強制的に非表示にし、スペースも占有しない */
            height: 0px !important; /* 念のため高さも0に */
        }
        .appview-container .main .block-container{
                    padding-top: 1rem; /* 全体の上下パディングは維持 */
                    padding-right: 3rem;
                    padding-left: 3rem;
                    padding-bottom: 1rem;
                }
                /* .reportview-container は古いStreamlitのクラス名かもしれないので、影響がなければ削除も検討 */
                .reportview-container {
                    padding-top: 0rem;
                    padding-right: 3rem;
                    padding-left: 3rem;
                    padding-bottom: 0rem;
                }
                header[data-testid="stHeader"] {
                    z-index: -1; /* メニューボタンなどが隠れないように調整が必要な場合がある */
                }
                /* ツールバーやデコレーションが他の要素の背後に隠れないように */
                div[data-testid="stToolbar"] {
                z-index: 100 !important; 
                }
                div[data-testid="stDecoration"] {
                z-index: 100 !important;
                }
        .block-container { /* Streamlitのメインコンテンツブロック */
                    padding-top: 0rem !important; /* タブ表示エリアの上下パディングを詰める */
                    padding-bottom: 0rem !important;
                }
        /* 画像間のスペース調整 */
        .stImage > img {
            margin-bottom: 10px; /* 画像の下に少し余白を追加 */
            border: 1px solid #eee; /* 画像に薄い枠線を追加 */
        }
        /* プルダウンと画像の間のスペースを詰める */
        div[data-testid="stImage"] { /* st.imageのコンテナ */
            margin-top: 0.25rem !important; /* 上マージンを少し詰める (デフォルトより小さく) */
        }
        </style>
        """
st.markdown(HIDE_ST_STYLE, unsafe_allow_html=True)
st.title(PAGE_TITLE)

def create_image_download_link(img_bytes: bytes, filename: str) -> str:
    """画像バイトデータからdata URLを生成して直接開けるリンクを作成"""
    try:
        # Base64エンコード
        b64_encoded = base64.b64encode(img_bytes).decode()
        # Data URLを作成
        data_url = f"data:image/png;base64,{b64_encoded}"
        return data_url
    except Exception as e:
        print(f"画像リンク作成エラー: {e}")
        return ""

def display_pdf(pdf_path: Path):
    """
    指定されたPDFファイルの各ページを高画質で画像に変換し、Streamlitで表示する。
    画像クリック時に直接開けるリンクを提供。
    """
    if not pdf_path.exists() or not pdf_path.is_file():
        st.error(f"PDFファイルが見つかりません: {pdf_path}")
        return

    try:
        doc = fitz.open(pdf_path)

        if doc.page_count == 0:
            st.warning("PDFからページを読み込めませんでした。ファイルが空か、破損している可能性があります。")
            doc.close()
            return

        # 高画質変換：3倍で鮮明に表示
        zoom_matrix = fitz.Matrix(3, 3)

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=zoom_matrix)  # type: ignore
            img_bytes = pix.tobytes("png")  # PNG画質を維持

            # Data URLを生成
            filename = f"{pdf_path.stem}_page_{page_num + 1}.png"
            data_url = create_image_download_link(img_bytes, filename)
            
            # 画像をクリック可能なリンクとして表示
            if data_url:
                st.markdown(
                    f'''<a href="{data_url}" target="_blank" style="display: block; text-decoration: none;">
                    <img src="{data_url}" style="width: 100%; cursor: pointer;" alt="ページ {page_num + 1}/{doc.page_count}" title="クリックで画像を新しいタブで開く">
                    </a>
                    <p style="font-size: 14px; color: #666; text-align: center; margin-top: 5px;">ページ {page_num + 1}/{doc.page_count}</p>''',
                    unsafe_allow_html=True
                )
            else:
                # フォールバック: 通常のst.image
                st.image(
                    img_bytes, 
                    caption=f"ページ {page_num + 1}/{doc.page_count}", 
                    use_container_width='always'
                )
            
            if page_num < doc.page_count - 1:
                st.markdown("---")

        doc.close()

    except Exception as e:
        st.error(f"PDFの画像変換・表示中に予期せぬエラーが発生しました ({pdf_path.name}): {e}")
        if 'doc' in locals() and doc:  # type: ignore
            doc.close()

def display_tif(tif_path: Path):
    """
    指定されたTIFファイルを画像として表示する。
    画像クリック時に直接開けるリンクを提供。
    """
    if not tif_path.exists() or not tif_path.is_file():
        st.error(f"TIFファイルが見つかりません: {tif_path}")
        return

    try:
        with Image.open(tif_path) as img:
            # 画像をPNGバイトデータに変換
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Data URLを生成
            filename = f"{tif_path.stem}.png"
            data_url = create_image_download_link(img_bytes, filename)
            
            # 画像をクリック可能なリンクとして表示
            if data_url:
                st.markdown(
                    f'''<a href="{data_url}" target="_blank" style="display: block; text-decoration: none;">
                    <img src="{data_url}" style="width: 100%; cursor: pointer;" alt="{tif_path.name}" title="クリックで画像を新しいタブで開く">
                    </a>
                    <p style="font-size: 14px; color: #666; text-align: center; margin-top: 5px;">{tif_path.name}</p>''',
                    unsafe_allow_html=True
                )
            else:
                # フォールバック: 通常のst.image
                st.image(img, caption=f"{tif_path.name}", use_container_width='always')
                
    except Exception as e:
        st.error(f"TIFファイルの表示中にエラーが発生しました ({tif_path.name}): {e}")

def display_file(file_path: Path):
    """
    ファイル拡張子に応じてPDFまたはTIFファイルを表示する。
    """
    extension = file_path.suffix.lower()
    if extension == '.pdf':
        display_pdf(file_path)
    elif extension in ['.tif', '.tiff']:
        display_tif(file_path)
    else:
        st.error(f"サポートされていないファイル形式です: {extension}")

def get_files_in_folder(folder_path: Path, extensions):
    """指定フォルダ内の指定拡張子のファイル名のリストを返す（フルパスも保持）"""
    if not folder_path.exists() or not folder_path.is_dir():
        return {}

    files_dict = {}
    try:
        for ext in extensions:
            for file_obj in list(folder_path.glob(f"*.{ext}")) + list(folder_path.glob(f"*.{ext.upper()}")):
                if file_obj.is_file() and file_obj.name not in files_dict:
                    files_dict[file_obj.name] = file_obj
    except Exception as e:
        st.error(f"フォルダ内のファイルリスト取得中にエラーが発生しました ({folder_path}): {e}")
    return files_dict

def get_folder_metadata(root_path: Path) -> Dict[str, float]:
    """各第1階層フォルダの更新時刻を取得"""
    metadata = {}
    if not root_path.exists() or not root_path.is_dir():
        return metadata
    
    try:
        for item in root_path.iterdir():
            if item.is_dir():
                metadata[item.name] = item.stat().st_mtime
    except Exception as e:
        print(f"メタデータ取得エラー: {e}")
    
    return metadata

def scan_folder_async(first_level_path: Path, folder_name: str) -> Tuple[str, Dict[str, List[str]]]:
    """単一の第1階層フォルダを非同期でスキャン（直下ファイル対応）"""
    return scan_folder_with_direct_files(first_level_path, folder_name)

async def scan_folder_structure_async(root_path: Path, changed_folders: List[str] = None) -> Dict[str, Dict[str, List[str]]]:
    """非同期でフォルダ構造をスキャン（差分更新対応）"""
    structure = {}
    
    if not root_path.exists() or not root_path.is_dir():
        return structure
    
    # 既存の構造を読み込み（差分更新の場合）
    if changed_folders and STRUCTURE_JSON_PATH.exists():
        try:
            with open(STRUCTURE_JSON_PATH, 'r', encoding='utf-8') as f:
                structure = json.load(f)
            print(f"既存構造読み込み: {len(structure)}個の分類")
        except Exception as e:
            print(f"既存構造読み込みエラー: {e}")
            structure = {}
    
    # スキャン対象フォルダを決定
    if changed_folders:
        target_folders = [(root_path / folder_name, folder_name) for folder_name in changed_folders 
                         if (root_path / folder_name).exists()]
        print(f"差分更新: {len(target_folders)}個のフォルダをスキャン")
    else:
        target_folders = [(item, item.name) for item in root_path.iterdir() if item.is_dir()]
        print(f"全体スキャン: {len(target_folders)}個のフォルダをスキャン")
    
    # 並列処理でスキャン
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            tasks = []
            for i, (first_level_path, folder_name) in enumerate(target_folders, 1):
                print(f"[{i}/{len(target_folders)}] 処理開始: {folder_name}")
                task = loop.run_in_executor(executor, scan_folder_async, first_level_path, folder_name)
                tasks.append(task)
            
            # 結果を取得
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    print(f"タスクエラー: {result}")
                    continue
                
                folder_name, folder_structure = result
                structure[folder_name] = folder_structure
                print(f"完了: {folder_name} ({len(folder_structure)} フォルダ)")
                
    finally:
        loop.close()
    
    print(f"スキャン完了: 全{len(structure)}個の第1階層フォルダを処理")
    return structure

def detect_folder_changes(root_path: Path) -> Tuple[List[str], Dict[str, float]]:
    """フォルダの変更を検出"""
    current_metadata = get_folder_metadata(root_path)
    changed_folders = []
    
    if not METADATA_JSON_PATH.exists():
        print("初回スキャン: メタデータファイルが存在しません")
        return list(current_metadata.keys()), current_metadata
    
    try:
        with open(METADATA_JSON_PATH, 'r', encoding='utf-8') as f:
            old_metadata = json.load(f)
    except Exception as e:
        print(f"メタデータ読み込みエラー: {e}")
        return list(current_metadata.keys()), current_metadata
    
    # 変更検出
    for folder_name, current_time in current_metadata.items():
        if folder_name not in old_metadata:
            print(f"新規フォルダ検出: {folder_name}")
            changed_folders.append(folder_name)
        elif abs(current_time - old_metadata[folder_name]) > 1:  # 1秒以上の差
            print(f"更新フォルダ検出: {folder_name}")
            changed_folders.append(folder_name)
    
    # 削除されたフォルダを検出
    deleted_folders = set(old_metadata.keys()) - set(current_metadata.keys())
    if deleted_folders:
        print(f"削除フォルダ検出: {deleted_folders}")
    
    if not changed_folders:
        print("変更なし: 既存の構造ファイルを使用")
    
    return changed_folders, current_metadata

def sync_fallback_scan(root_path: Path, changed_folders: List[str] = None) -> Dict[str, Dict[str, List[str]]]:
    """同期処理でのフォールバックスキャン"""
    print("同期スキャン開始...")
    structure = {}
    
    # 既存の構造を読み込み（差分更新の場合）
    if changed_folders and STRUCTURE_JSON_PATH.exists():
        try:
            with open(STRUCTURE_JSON_PATH, 'r', encoding='utf-8') as f:
                structure = json.load(f)
            print(f"既存構造読み込み: {len(structure)}個の分類")
        except Exception as e:
            print(f"既存構造読み込みエラー: {e}")
            structure = {}
    
    # スキャン対象フォルダを決定
    if changed_folders:
        target_folders = [(root_path / folder_name, folder_name) for folder_name in changed_folders 
                         if (root_path / folder_name).exists()]
        print(f"同期差分更新: {len(target_folders)}個のフォルダをスキャン")
    else:
        target_folders = [(item, item.name) for item in root_path.iterdir() if item.is_dir()]
        print(f"同期全体スキャン: {len(target_folders)}個のフォルダをスキャン")
    
    # 順次処理でスキャン
    for i, (first_level_path, folder_name) in enumerate(target_folders, 1):
        print(f"[{i}/{len(target_folders)}] 処理中: {folder_name}")
        try:
            folder_name, folder_structure = scan_folder_with_direct_files(first_level_path, folder_name)
            structure[folder_name] = folder_structure
            print(f"完了: {folder_name} ({len(folder_structure)} フォルダ)")
        except Exception as e:
            print(f"フォルダスキャンエラー ({folder_name}): {e}")
            continue
    
    print(f"同期スキャン完了: 全{len(structure)}個の第1階層フォルダを処理")
    return structure

def scan_folder_with_direct_files(first_level_path: Path, folder_name: str) -> Tuple[str, Dict[str, List[str]]]:
    """第1階層フォルダとその直下のファイルもスキャンする"""
    folder_structure = {}
    
    try:
        # 第1階層直下のファイルをチェック
        direct_files = []
        file_extensions = ['pdf', 'tif', 'tiff']
        for ext in file_extensions:
            try:
                for file_obj in list(first_level_path.glob(f"*.{ext}")) + list(first_level_path.glob(f"*.{ext.upper()}")):
                    if file_obj.is_file():
                        direct_files.append(file_obj.name)
            except Exception:
                continue
        
        # 直下にファイルがある場合は特別なキーで保存
        if direct_files:
            folder_structure["__direct_files__"] = sorted(direct_files)
            print(f"      └─ 直下ファイル数: {len(direct_files)}")
        
        # 第2階層フォルダをスキャン
        second_level_folders = [item for item in first_level_path.iterdir() if item.is_dir()]
        total_second_level = len(second_level_folders)
        
        if total_second_level > 0:
            print(f"  └─ {folder_name}: 第2階層フォルダ数 {total_second_level}")
        
        for j, second_level_item in enumerate(second_level_folders, 1):
            second_level_name = second_level_item.name
            
            # 進捗表示
            if total_second_level <= 10 or j % max(1, total_second_level // 10) == 0 or j == total_second_level:
                print(f"    [{j}/{total_second_level}] {second_level_name}")
            
            # ファイルリストを取得
            files = []
            for ext in file_extensions:
                try:
                    for file_obj in list(second_level_item.glob(f"*.{ext}")) + list(second_level_item.glob(f"*.{ext.upper()}")):
                        if file_obj.is_file():
                            files.append(file_obj.name)
                except Exception:
                    continue
            
            folder_structure[second_level_name] = sorted(files)
            
            if len(files) > 0:
                print(f"      └─ ファイル数: {len(files)}")
                
    except Exception as e:
        print(f"フォルダスキャンエラー ({folder_name}): {e}")
    
    return folder_name, folder_structure

def should_auto_update():
    """5分に一回の自動更新チェック"""
    if not STRUCTURE_JSON_PATH.exists():
        return True  # 初回は必ず更新
    
    try:
        structure_mod_time = STRUCTURE_JSON_PATH.stat().st_mtime
        current_time = time.time()
        elapsed = current_time - structure_mod_time
        
        if elapsed >= AUTO_UPDATE_INTERVAL:
            print(f"自動更新実行: 前回更新から {elapsed/60:.1f}分経過")
            return True
        else:
            remaining = (AUTO_UPDATE_INTERVAL - elapsed) / 60
            print(f"自動更新まで残り {remaining:.1f}分")
            return False
    except Exception as e:
        print(f"自動更新チェックエラー: {e}")
        return True

def load_or_create_structure(root_path: Path, force_update: bool = False):
    """差分更新と非同期処理でフォルダ構造を読み込む、または作成する"""
    
    # 初回チェック：JSONファイルが存在しない場合は同期処理で作成
    is_first_run = not STRUCTURE_JSON_PATH.exists()
    
    if is_first_run:
        print("=" * 60)
        print("初回実行：同期処理でフォルダ構造を作成します")
        print("=" * 60)
        
        # 初回は同期スキャンを実行
        structure = sync_fallback_scan(root_path)
        
        # 構造ファイルとメタデータを保存
        current_metadata = get_folder_metadata(root_path)
        try:
            with open(STRUCTURE_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(structure, f, ensure_ascii=False, indent=2)
            print(f"初回構造ファイル保存完了: {STRUCTURE_JSON_PATH}")
            
            with open(METADATA_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(current_metadata, f, ensure_ascii=False, indent=2)
            print(f"初回メタデータファイル保存完了: {METADATA_JSON_PATH}")
            
            total_folders = sum(len(v) for v in structure.values())
            print(f"初回スキャン完了: {len(structure)}個の分類、合計{total_folders}個のフォルダ")
            
        except Exception as e:
            print(f"初回ファイル保存エラー: {e}")
        
        return structure
    
    # 2回目以降：非同期処理を使用
    # 強制更新でない場合は自動更新チェック
    if not force_update and not should_auto_update():
        try:
            with open(STRUCTURE_JSON_PATH, 'r', encoding='utf-8') as f:
                structure = json.load(f)
            print(f"既存構造使用: {len(structure)}個の分類（次回自動更新まで待機）")
            return structure
        except Exception as e:
            print(f"既存構造読み込みエラー: {e}")
            # エラーの場合は強制更新
            force_update = True
    
    print("=" * 60)
    print("フォルダ構造の差分チェック開始（2回目以降：非同期処理）")
    print("=" * 60)
    
    # フォルダの変更を検出
    changed_folders, current_metadata = detect_folder_changes(root_path)
    
    # 強制更新でない場合で変更がない場合は既存のJSONを読み込み
    if not force_update and not changed_folders and STRUCTURE_JSON_PATH.exists():
        try:
            with open(STRUCTURE_JSON_PATH, 'r', encoding='utf-8') as f:
                structure = json.load(f)
            print(f"構造ファイル読み込み完了: {len(structure)}個の分類（変更なし）")
            # メタデータのタイムスタンプを更新（次回の5分カウント用）
            with open(METADATA_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(current_metadata, f, ensure_ascii=False, indent=2)
            return structure
        except Exception as e:
            print(f"構造ファイル読み込みエラー: {e}")
    
    # 非同期スキャンを実行
    print("=" * 60)
    print("フォルダ構造スキャン開始（並列処理）")
    print("=" * 60)
    
    try:
        # 非同期スキャンを実行
        print("非同期スキャン開始...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            structure = loop.run_until_complete(scan_folder_structure_async(root_path, changed_folders))
            print(f"非同期スキャン完了: {len(structure)}個の分類取得")
        finally:
            loop.close()
            
    except Exception as e:
        print(f"非同期スキャンエラー: {e}")
        import traceback
        print("エラー詳細:")
        traceback.print_exc()
        
        # フォールバック: 同期スキャンを実行
        print("フォールバック: 同期スキャンを試行します")
        structure = sync_fallback_scan(root_path, changed_folders)
    
    print("=" * 60)
    print("フォルダ構造スキャン完了")
    print("=" * 60)
    
    # 構造ファイルとメタデータを保存
    try:
        with open(STRUCTURE_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)
        print(f"構造ファイル保存完了: {STRUCTURE_JSON_PATH}")
        
        with open(METADATA_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_metadata, f, ensure_ascii=False, indent=2)
        print(f"メタデータファイル保存完了: {METADATA_JSON_PATH}")
        
        total_folders = sum(len(v) for v in structure.values())
        print(f"最終結果: {len(structure)}個の分類、合計{total_folders}個のフォルダ")
        
    except Exception as e:
        print(f"ファイル保存エラー: {e}")
    
    return structure

def load_structure_with_diff_update_only(root_path: Path):
    """真の差分更新：変更があったフォルダのみ更新"""
    print("=" * 60)
    print("差分更新実行：変更検出中...")
    print("=" * 60)
    
    # フォルダの変更を検出
    changed_folders, current_metadata = detect_folder_changes(root_path)
    
    if not changed_folders:
        print("変更なし：既存データを使用します")
        try:
            with open(STRUCTURE_JSON_PATH, 'r', encoding='utf-8') as f:
                structure = json.load(f)
            print(f"差分更新完了: 変更なし ({len(structure)}個の分類)")
            return structure
        except Exception as e:
            print(f"既存構造読み込みエラー: {e}")
            return {}
    
    # 変更があった場合のみスキャン実行
    print(f"変更検出: {len(changed_folders)}個のフォルダを更新します")
    
    try:
        # 非同期スキャンを実行（差分のみ）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            structure = loop.run_until_complete(scan_folder_structure_async(root_path, changed_folders))
            print(f"差分更新完了: {len(changed_folders)}個のフォルダを更新")
        finally:
            loop.close()
            
    except Exception as e:
        print(f"差分更新エラー: {e}")
        # フォールバック: 同期差分更新
        structure = sync_fallback_scan(root_path, changed_folders)
    
    # 構造ファイルとメタデータを保存
    try:
        with open(STRUCTURE_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)
        
        with open(METADATA_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"差分更新保存完了")
        
    except Exception as e:
        print(f"差分更新保存エラー: {e}")
    
    return structure

# --- メイン処理 ---
root_dir = Path(ROOT_DIR_PATH_STR)

if not root_dir.exists() or not root_dir.is_dir():
    st.error(f"指定されたルートフォルダが見つかりません。パスを確認してください: {ROOT_DIR_PATH_STR}")
    st.stop()

# 真の5分間隔自動更新を実装（session_state使用）
if 'last_update_check' not in st.session_state:
    print("初回起動: セッション状態を初期化")
    st.session_state.last_update_check = time.time()
    st.session_state.structure = load_or_create_structure(root_dir)
else:
    # 5分経過チェック
    current_time = time.time()
    elapsed = current_time - st.session_state.last_update_check
    
    if elapsed >= AUTO_UPDATE_INTERVAL:
        print(f"自動更新実行: 前回更新から {elapsed/60:.1f}分経過")
        st.session_state.structure = load_or_create_structure(root_dir)
        st.session_state.last_update_check = current_time
    else:
        remaining = (AUTO_UPDATE_INTERVAL - elapsed) / 60
        print(f"キャッシュ使用: 自動更新まで残り {remaining:.1f}分")

# セッション状態から構造を取得
structure = st.session_state.structure

# デバッグ情報を表示（コンソールのみ）
if structure:
    print(f"デバッグ: 構造使用中 - {len(structure)}個の分類")
else:
    print("デバッグ: 構造が空です")
    st.error("フォルダ構造が取得できませんでした。コンソールでエラー詳細を確認してください。")
    
    # JSONファイルの状態を表示
    if STRUCTURE_JSON_PATH.exists():
        size = STRUCTURE_JSON_PATH.stat().st_size
        st.warning(f"JSONファイルは存在しますが、サイズ: {size}バイト")
        print(f"デバッグ: JSONファイルサイズ {size}バイト")
    
    st.stop()


# 図面選択UI
st.markdown("##### 図面選択")

# 第1階層フォルダの選択
first_level_folders = sorted(structure.keys())
if not first_level_folders:
    st.error("第1階層にフォルダが見つかりませんでした。")
    st.stop()

# プルダウンを2:2:3の比率で配置
col1, col2, col3 = st.columns([2, 2, 3])

with col1:
    selected_first_level = st.selectbox(
        "第一階層フォルダ選択:",
        options=["選択してください"] + first_level_folders,
        key="selected_first_level"
    )

# 第2階層の選択肢を取得
second_level_options = []
if selected_first_level and selected_first_level != "選択してください":
    all_second_level = sorted(structure[selected_first_level].keys())
    # 直下のファイルがある場合は特別な選択肢を追加
    if "__direct_files__" in all_second_level:
        second_level_options.append("直下のファイル")
        all_second_level.remove("__direct_files__")
    second_level_options.extend(all_second_level)

with col2:
    if second_level_options:
        selected_second_level = st.selectbox(
            "第二階層フォルダ選択:",
            options=["選択してください"] + second_level_options,
            key="selected_second_level"
        )
    else:
        st.selectbox("第二階層フォルダ選択:", ["選択してください"], disabled=True, key="selected_second_level_disabled")
        selected_second_level = None

# ファイルの選択肢を取得
files_list = []
if selected_first_level and selected_first_level != "選択してください" and selected_second_level and selected_second_level != "選択してください":
    if selected_second_level == "直下のファイル":
        files_list = structure[selected_first_level].get("__direct_files__", [])
    else:
        files_list = structure[selected_first_level].get(selected_second_level, [])

with col3:
    if files_list:
        selected_file = st.selectbox(
            "ファイルを選択:",
            options=["選択してください"] + files_list,
            key="selected_file"
        )
    else:
        st.selectbox("ファイルを選択:", ["選択してください"], disabled=True, key="selected_file_disabled")
        selected_file = None

# ファイル表示判定
show_file = (selected_first_level and selected_first_level != "選択してください" and 
            selected_second_level and selected_second_level != "選択してください" and
            selected_file and selected_file != "選択してください")

# 画像表示エリア（プルダウンの下）
if show_file:
    # ファイルパスを構築
    if selected_second_level == "直下のファイル":
        file_path = root_dir / selected_first_level / selected_file
        display_path = f"{selected_first_level}/{selected_file}"
    else:
        file_path = root_dir / selected_first_level / selected_second_level / selected_file
        display_path = f"{selected_first_level}/{selected_second_level}/{selected_file}"
    
    st.markdown(f"<p style='font-size:12px; color:gray;'>表示中: {display_path}</p>", unsafe_allow_html=True)
    
    display_file(file_path)
else:
    # ファイルが表示されていない場合のスペース
    st.write("")  # 空行
    st.write("")  # 空行
    st.write("")  # 空行

# 更新ボタンとステータス表示
st.markdown("---")

# 手動更新ボタンとシステム情報を横並びに配置
bottom_col1, bottom_col2 = st.columns([1, 2])

with bottom_col1:
    if st.button("手動更新"):
        # 真の差分更新：変更があったフォルダのみ更新
        print("手動更新実行")
        st.session_state.structure = load_structure_with_diff_update_only(root_dir)
        st.session_state.last_update_check = time.time()
        st.rerun()
    st.caption("※5分に1回自動更新されます")

with bottom_col2:
    # システム情報を横並びで表示
    st.markdown("**システム情報**")
    info_col1, info_col2, info_col3 = st.columns(3)
    
    with info_col1:
        st.caption(f"**ルートフォルダ**")
        st.caption(f"{ROOT_DIR_PATH_STR}")

    with info_col2:
        if STRUCTURE_JSON_PATH.exists():
            mod_time = STRUCTURE_JSON_PATH.stat().st_mtime
            st.caption(f"**構造ファイル更新**")
            st.caption(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(mod_time))}")
        else:
            st.caption(f"**構造ファイル更新**")
            st.caption("未作成")

    with info_col3:
        if METADATA_JSON_PATH.exists():
            meta_mod_time = METADATA_JSON_PATH.stat().st_mtime
            st.caption(f"**メタデータ更新**")
            st.caption(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(meta_mod_time))}")
        else:
            st.caption(f"**メタデータ更新**")
            st.caption("未作成")
