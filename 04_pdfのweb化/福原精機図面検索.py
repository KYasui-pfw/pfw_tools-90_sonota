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
from typing import Dict, List, Tuple
from datetime import datetime
import pytz

# --- 設定項目 ---
ROOT_DIR_PATH_STR = r"/app/network/zumen"
HAIZU_ROOT_DIR_PATH_STR = r"/app/network/zumenhai"
PAGE_TITLE = "福原精機図面検索"
STRUCTURE_JSON_PATH = Path(r"/app/file_monitor/zumen") / "folder_structure.json"
METADATA_JSON_PATH = Path(r"/app/file_monitor/zumen") / "folder_metadata.json"
HAIZU_STRUCTURE_JSON_PATH = Path(r"/app/file_monitor/zumenhai") / "haizu_folder_structure.json"
HAIZU_METADATA_JSON_PATH = Path(r"/app/file_monitor/zumenhai") / "haizu_folder_metadata.json"


def format_jst_time(timestamp):
    """UNIXタイムスタンプを日本時間の文字列に変換"""
    jst = pytz.timezone('Asia/Tokyo')
    dt_utc = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
    dt_jst = dt_utc.astimezone(jst)
    return dt_jst.strftime('%Y-%m-%d %H:%M:%S JST')


# --- Streamlit ページ設定 ---
st.set_page_config(page_title=PAGE_TITLE, page_icon="📋", layout="wide")

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

# iPad Safari用のfavicon対応
favicon_html = """
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📋</text></svg>">
<link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📋</text></svg>">
"""
st.markdown(favicon_html, unsafe_allow_html=True)
st.title(PAGE_TITLE)

def display_pdf(pdf_path: Path):
    """
    指定されたPDFファイルの各ページを高画質で画像に変換し、Streamlitで表示する。
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

            # Base64エンコードして高画質で表示
            b64_encoded = base64.b64encode(img_bytes).decode()
            data_url = f"data:image/png;base64,{b64_encoded}"
            
            # 高画質画像を直接表示（リンクなし）
            st.markdown(
                f'''<div style="margin-bottom: 20px;">
                    <img src="{data_url}" style="width: 100%; border: 1px solid #eee;" 
                         alt="ページ {page_num + 1}/{doc.page_count}">
                    <p style="font-size: 14px; color: #666; text-align: center; margin-top: 5px;">ページ {page_num + 1}/{doc.page_count}</p>
                </div>''',
                unsafe_allow_html=True
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
    破損したファイルでも可能な限り表示を試行する。
    """
    if not tif_path.exists() or not tif_path.is_file():
        st.error(f"TIFファイルが見つかりません: {tif_path}")
        return

    # 最初に通常の方法で読み込み試行
    try:
        file_size = tif_path.stat().st_size
        if file_size == 0:
            st.error(f"TIFファイルが空です: {tif_path.name}")
            return

        with Image.open(tif_path) as img:
            # 画像をPNGバイトデータに変換
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Base64エンコードして高画質で表示
            b64_encoded = base64.b64encode(img_bytes).decode()
            data_url = f"data:image/png;base64,{b64_encoded}"
            
            # 高画質画像を直接表示
            st.markdown(
                f'''<div style="margin-bottom: 20px;">
                    <img src="{data_url}" style="width: 100%; border: 1px solid #eee;" 
                         alt="{tif_path.name}">
                    <p style="font-size: 14px; color: #666; text-align: center; margin-top: 5px;">{tif_path.name}</p>
                </div>''',
                unsafe_allow_html=True
            )
            return  # 成功時はここで終了

    except Exception as e:
        st.warning(f"通常読み込みでエラーが発生しました ({tif_path.name}): {e}")

    # 破損許容モードで再試行
    try:
        # ImageFileクラスのLOAD_TRUNCATED_IMAGESを有効にする
        from PIL import ImageFile
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        
        with Image.open(tif_path) as img:
            # 可能な限り画像データを読み込み
            try:
                img.load()  # 画像データを強制読み込み
                st.success("破損許容モードで正常に読み込みました")
            except Exception:
                st.warning("一部のデータが破損していますが、可能な部分を表示します")
            
            # PNGに変換
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Base64エンコードして表示
            b64_encoded = base64.b64encode(img_bytes).decode()
            data_url = f"data:image/png;base64,{b64_encoded}"
            
            # 注意書きと共に表示
            st.markdown(
                f'''<div style="margin-bottom: 20px;">
                    <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 8px; margin-bottom: 8px; border-radius: 4px;">
                        <small>⚠️ このファイルは部分的に破損している可能性があります</small>
                    </div>
                    <img src="{data_url}" style="width: 100%; border: 1px solid #eee;" 
                         alt="{tif_path.name}">
                    <p style="font-size: 14px; color: #666; text-align: center; margin-top: 5px;">{tif_path.name}</p>
                </div>''',
                unsafe_allow_html=True
            )

    except Exception as final_error:
        st.error(f"破損許容モードでも読み込みできませんでした ({tif_path.name}): {final_error}")
        st.warning("⚠️ ファイルが重度に破損しているか、サポートされていない形式です")

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



def load_structure_from_json(json_path, data_type="図面"):
    """JSONファイルから構造を読み込み"""
    print("=" * 60)
    print(f"{data_type}のJSONファイルからデータを読み込み中...")
    print("=" * 60)
    
    try:
        # JSONファイルが存在するかチェック
        if not json_path.exists():
            print(f"警告: {data_type}のJSONファイルが見つかりません")
            print(f"パス: {json_path}")
            return {}
        
        # JSONファイルを読み込み
        with open(json_path, 'r', encoding='utf-8') as f:
            structure = json.load(f)
        
        # ファイルの最終更新時刻を確認
        file_mtime = json_path.stat().st_mtime
        current_time = time.time()
        age_minutes = (current_time - file_mtime) / 60
        
        print(f"{data_type}のJSONファイル読み込み完了: {len(structure)}個の分類")
        print(f"データ最終更新: {age_minutes:.1f}分前")
        
        if age_minutes > 60:  # 1時間以上古い
            print("⚠️ 警告: データが古い可能性があります")
        
        return structure
        
    except json.JSONDecodeError as e:
        print(f"{data_type}のJSONファイル解析エラー: {e}")
        print("JSONファイルが破損している可能性があります")
        return {}
    except Exception as e:
        print(f"{data_type}のデータ読み込みエラー: {e}")
        return {}

def search_files_in_structure(structure, search_text, search_mode):
    """
    フォルダ構造からファイル名を検索する
    Args:
        structure: JSONから読み込んだフォルダ構造
        search_text: 検索テキスト
        search_mode: "前方一致" または "部分一致"
    Returns:
        list: マッチしたファイルのパス一覧 ["フォルダパス/ファイル名", ...]
    """
    if not search_text or len(search_text) < 3:
        return []
    
    search_text_lower = search_text.lower()
    matched_files = []
    
    for first_level, second_level_dict in structure.items():
        for second_level, files in second_level_dict.items():
            if not isinstance(files, list):
                continue
                
            for filename in files:
                filename_lower = filename.lower()
                
                # 検索条件チェック
                if search_mode == "前方一致":
                    match = filename_lower.startswith(search_text_lower)
                else:  # 部分一致
                    match = search_text_lower in filename_lower
                
                if match:
                    if second_level == "__direct_files__":
                        file_path = f"{first_level}/{filename}"
                    else:
                        file_path = f"{first_level}/{second_level}/{filename}"
                    matched_files.append(file_path)
    
    # ファイル名でソート
    return sorted(matched_files)


# --- メイン処理 ---

# タブUI
tab1, tab2 = st.tabs(["図面選択", "図面検索"])

with tab1:
    # 4つのプルダウンを横一列に配置
    col0, col1, col2, col3 = st.columns([1.5, 2, 2, 3])

    with col0:
        diagram_type = st.selectbox(
            "種別:",
            options=["図面", "廃図"],
            key="diagram_type",
            index=0  # 初期値は「図面」
        )

    # 図面種別に応じたパスとJSONファイルを取得
    if diagram_type == "図面":
        current_root_dir = Path(ROOT_DIR_PATH_STR)
        current_structure_json = STRUCTURE_JSON_PATH
        current_metadata_json = METADATA_JSON_PATH
        session_key_structure = 'structure'
        session_key_mtime = 'last_json_mtime'
    else:  # 廃図
        current_root_dir = Path(HAIZU_ROOT_DIR_PATH_STR)
        current_structure_json = HAIZU_STRUCTURE_JSON_PATH
        current_metadata_json = HAIZU_METADATA_JSON_PATH
        session_key_structure = 'haizu_structure'
        session_key_mtime = 'haizu_last_json_mtime'

    # ルートディレクトリの存在チェック
    if not current_root_dir.exists() or not current_root_dir.is_dir():
        st.error(f"指定されたルートフォルダが見つかりません。パスを確認してください: {current_root_dir}")
        st.stop()

    # JSONファイルからのデータロード
    if session_key_structure not in st.session_state:
        print(f"初回起動: {diagram_type}のJSONデータを読み込み")
        st.session_state[session_key_structure] = load_structure_from_json(current_structure_json, diagram_type)
        st.session_state[session_key_mtime] = current_structure_json.stat().st_mtime if current_structure_json.exists() else 0
    else:
        # JSONファイルの更新チェック（軽量）
        try:
            current_json_mtime = current_structure_json.stat().st_mtime if current_structure_json.exists() else 0
            if current_json_mtime > st.session_state[session_key_mtime]:
                print(f"{diagram_type}のJSONファイルが更新されました - データを再読み込み")
                st.session_state[session_key_structure] = load_structure_from_json(current_structure_json, diagram_type)
                st.session_state[session_key_mtime] = current_json_mtime
            else:
                print(f"キャッシュ使用: {diagram_type}のJSONファイルに変更なし")
        except Exception as e:
            print(f"{diagram_type}のJSONファイルチェックエラー: {e}")

    # セッション状態から構造を取得
    structure = st.session_state[session_key_structure]

    # デバッグ情報を表示（コンソールのみ）
    if structure:
        print(f"デバッグ: {diagram_type}構造使用中 - {len(structure)}個の分類")
    else:
        print(f"デバッグ: {diagram_type}構造が空です")
        st.error(f"{diagram_type}のフォルダ構造が取得できませんでした。コンソールでエラー詳細を確認してください。")
        
        # JSONファイルの状態を表示
        if current_structure_json.exists():
            size = current_structure_json.stat().st_size
            st.warning(f"{diagram_type}のJSONファイルは存在しますが、サイズ: {size}バイト")
            print(f"デバッグ: {diagram_type}のJSONファイルサイズ {size}バイト")
        
        st.stop()

    # 第1階層フォルダの選択
    first_level_folders = sorted(structure.keys())
    if not first_level_folders:
        st.error("第1階層にフォルダが見つかりませんでした。")
        st.stop()

    with col1:
        selected_first_level = st.selectbox(
            "第一階層フォルダ:",
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
                "第二階層フォルダ:",
                options=["選択してください"] + second_level_options,
                key="selected_second_level"
            )
        else:
            st.selectbox("第二階層フォルダ:", ["選択してください"], disabled=True, key="selected_second_level_disabled")
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
            file_path = current_root_dir / selected_first_level / selected_file
            display_path = f"{selected_first_level}/{selected_file}"
        else:
            file_path = current_root_dir / selected_first_level / selected_second_level / selected_file
            display_path = f"{selected_first_level}/{selected_second_level}/{selected_file}"
        
        # リンク用URLの構築
        if diagram_type == "廃図":
            file_url = f"http://fsrv24/zumenhai/{display_path}"
            st.markdown(f"<p style='font-size:12px; color:gray;'>廃図表示中: <a href='{file_url}' target='_blank'>{display_path}</a></p>", unsafe_allow_html=True)
        else:
            file_url = f"http://fsrv24/zumen/{display_path}"
            st.markdown(f"<p style='font-size:12px; color:gray;'>表示中: <a href='{file_url}' target='_blank'>{display_path}</a></p>", unsafe_allow_html=True)
        
        display_file(file_path)
    else:
        # ファイルが表示されていない場合のスペース
        st.write("")  # 空行
        st.write("")  # 空行
        st.write("")  # 空行

    # システム情報表示
    st.markdown("---")

    st.markdown("**システム情報**")
    info_col1, info_col2, info_col3 = st.columns(3)

    with info_col1:
        st.caption(f"**ルートフォルダ（{diagram_type}）**")
        st.caption(f"{current_root_dir}")

    with info_col2:
        if current_structure_json.exists():
            mod_time = current_structure_json.stat().st_mtime
            st.caption(f"**構造ファイル更新**")
            st.caption(f"{format_jst_time(mod_time)}")
        else:
            st.caption(f"**構造ファイル更新**")
            st.caption("未作成")

    with info_col3:
        if current_metadata_json.exists():
            meta_mod_time = current_metadata_json.stat().st_mtime
            st.caption(f"**メタデータ更新**")
            st.caption(f"{format_jst_time(meta_mod_time)}")
        else:
            st.caption(f"**メタデータ更新**")
            st.caption("未作成")

with tab2:
    # 検索UIレイアウト - 3列構成
    search_col1, search_col2, search_col3 = st.columns([1.5, 3.5,3.5])
    
    with search_col1:
        search_diagram_type = st.selectbox(
            "種別:",
            options=["図面", "廃図"],
            key="search_diagram_type",
            index=0  # 初期値は「図面」
        )
    
    with search_col2:
        # 真ん中の列を2分割
        search_sub_col1, search_sub_col2 = st.columns([1.5, 2])
        
        with search_sub_col1:
            search_mode = st.radio(
                "検索方式:",
                options=["部分一致", "前方一致"],
                key="search_mode",
                horizontal=False
            )
        
        with search_sub_col2:
            search_text = st.text_input(
                "ファイル名検索:",
                placeholder="ファイル名を入力（3文字以上）",
                key="search_text"
            )
    
    # 検索種別に応じた構造データを取得
    if search_diagram_type == "図面":
        search_current_root_dir = Path(ROOT_DIR_PATH_STR)
        search_current_structure_json = STRUCTURE_JSON_PATH
        search_current_metadata_json = METADATA_JSON_PATH
        search_session_key_structure = 'structure'
        search_session_key_mtime = 'last_json_mtime'
    else:  # 廃図
        search_current_root_dir = Path(HAIZU_ROOT_DIR_PATH_STR)
        search_current_structure_json = HAIZU_STRUCTURE_JSON_PATH
        search_current_metadata_json = HAIZU_METADATA_JSON_PATH
        search_session_key_structure = 'haizu_structure'
        search_session_key_mtime = 'haizu_last_json_mtime'

    # データロード（図面選択と同じロジック）
    if search_session_key_structure not in st.session_state:
        st.session_state[search_session_key_structure] = load_structure_from_json(search_current_structure_json, search_diagram_type)
        st.session_state[search_session_key_mtime] = search_current_structure_json.stat().st_mtime if search_current_structure_json.exists() else 0
    
    search_structure = st.session_state[search_session_key_structure]
    
    # 検索実行
    search_results = []
    if search_text and len(search_text) >= 3:
        search_results = search_files_in_structure(search_structure, search_text, search_mode)
    
    with search_col3:
        if search_results:
            selected_search_file = st.selectbox(
                f"検索結果: {len(search_results)}件",
                options=["選択してください"] + search_results,
                key="selected_search_file"
            )
        else:
            if search_text and len(search_text) >= 3:
                st.selectbox(
                    "検索結果: 0件",
                    options=["該当なし"],
                    disabled=True,
                    key="no_search_results"
                )
            else:
                if search_text and len(search_text) < 3:
                    st.selectbox(
                        "検索結果: (3文字以上入力)",
                        options=["検索してください"],
                        disabled=True,
                        key="search_results_placeholder"
                    )
                else:
                    st.selectbox(
                        "検索結果:",
                        options=["検索してください"],
                        disabled=True,
                        key="search_results_placeholder_initial"
                    )
    
    # 検索結果のファイル表示処理
    show_search_file = (search_results and 
                       'selected_search_file' in locals() and 
                       selected_search_file and 
                       selected_search_file != "選択してください")
    
    if show_search_file:
        # 選択されたファイルパスを解析してファイル名とパスを取得
        file_path_parts = selected_search_file.split('/')
        if len(file_path_parts) == 2:  # 直下のファイル
            first_level, filename = file_path_parts
            search_file_path = search_current_root_dir / first_level / filename
        else:  # サブフォルダ内のファイル
            first_level, second_level, filename = file_path_parts
            search_file_path = search_current_root_dir / first_level / second_level / filename
        
        # リンク用URLの構築（検索結果）
        if search_diagram_type == "廃図":
            search_file_url = f"http://fsrv24/zumenhai/{selected_search_file}"
            st.markdown(f"<p style='font-size:12px; color:gray;'>廃図表示中: <a href='{search_file_url}' target='_blank'>{selected_search_file}</a></p>", unsafe_allow_html=True)
        else:
            search_file_url = f"http://fsrv24/zumen/{selected_search_file}"
            st.markdown(f"<p style='font-size:12px; color:gray;'>表示中: <a href='{search_file_url}' target='_blank'>{selected_search_file}</a></p>", unsafe_allow_html=True)
        
        display_file(search_file_path)
    else:
        # ファイルが表示されていない場合のスペース
        st.write("")  # 空行
        st.write("")  # 空行
        st.write("")  # 空行
    
    # システム情報表示（検索タブも同様）
    st.markdown("---")
    
    st.markdown("**システム情報**")
    search_info_col1, search_info_col2, search_info_col3 = st.columns(3)
    
    with search_info_col1:
        st.caption(f"**ルートフォルダ（{search_diagram_type}）**")
        st.caption(f"{search_current_root_dir}")
    
    with search_info_col2:
        if search_current_structure_json.exists():
            search_mod_time = search_current_structure_json.stat().st_mtime
            st.caption(f"**構造ファイル更新**")
            st.caption(f"{format_jst_time(search_mod_time)}")
        else:
            st.caption(f"**構造ファイル更新**")
            st.caption("未作成")
    
    with search_info_col3:
        if search_current_metadata_json.exists():
            search_meta_mod_time = search_current_metadata_json.stat().st_mtime
            st.caption(f"**メタデータ更新**")
            st.caption(f"{format_jst_time(search_meta_mod_time)}")
        else:
            st.caption(f"**メタデータ更新**")
            st.caption("未作成")
