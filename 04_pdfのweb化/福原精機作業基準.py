import streamlit as st
import base64
import os
from pathlib import Path
import glob
import fitz  # PyMuPDF
# from PIL import Image, ImageOps # 余白トリミング関数で使用するためコメントアウト
# import io # 余白トリミング関数で使用するためコメントアウト

# --- 設定項目 ---
ROOT_DIR_PATH_STR = r"/app/network/kijyun"
PAGE_TITLE = "福原精機作業基準"

# 表示用のタブ名リスト (英文字2文字と発行台帳・配布票の後ろに全角スペース)
TAB_NAMES_FOR_DISPLAY = ["EA　", "EC　", "EG　", "EI　",
                         "EK　", "EM　", "ES　", "EW　", "発行台帳　", "配布票　"]
# 内部ロジックで使用するタブ名リスト (スペースなし)
TAB_NAMES_FOR_LOGIC = ["EA", "EC", "EG", "EI",
                       "EK", "EM", "ES", "EW", "発行台帳", "配布票"]

KIJUN_CHECK_HYO_PARENT_FOLDER_NAME = "基準チェック表 FS-　ーＰＤＦー"  # ルートフォルダ直下のこの名前のフォルダ

# --- Streamlit ページ設定 ---
st.set_page_config(page_title=PAGE_TITLE, page_icon="📝", layout="wide")

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
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📝</text></svg>">
<link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📝</text></svg>">
"""
st.markdown(favicon_html, unsafe_allow_html=True)
st.title(PAGE_TITLE)

def display_pdf(pdf_path: Path):
    """
    指定されたPDFファイルの各ページを画像に変換し、Streamlitで表示する (PyMuPDFを使用)。
    画質を調整し、進捗メッセージを非表示にする。
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

        zoom_matrix = fitz.Matrix(2, 2)  # 画質を2倍に変更

        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=zoom_matrix)  # type: ignore
            img_bytes = pix.tobytes("png")

            # 画像の上下余白をトリミングする処理を削除
            # trimmed_img_bytes = trim_image_whitespace_top_bottom(img_bytes)

            # img_bytes を直接使用
            st.image(
                img_bytes, caption=f"ページ {page_num + 1}/{doc.page_count}", use_column_width=True)
            if page_num < doc.page_count - 1:
                st.markdown("---")

        doc.close()

    except Exception as e:
        st.error(f"PDFの画像変換・表示中に予期せぬエラーが発生しました ({pdf_path.name}): {e}")
        if 'doc' in locals() and doc:  # type: ignore
            doc.close()


def find_latest_pdf_with_keyword(folder_path: Path, keyword: str):
    """指定フォルダ内で、名前にキーワードを含む最新のPDFファイルパスを返す"""
    if not folder_path.exists() or not folder_path.is_dir():
        st.warning(f"フォルダが見つかりません: {folder_path}")
        return None

    latest_file = None
    latest_time = 0

    try:
        for pdf_file in folder_path.glob(f"*{keyword}*.pdf"):
            if pdf_file.is_file():
                try:
                    mod_time = pdf_file.stat().st_mtime
                    if mod_time > latest_time:
                        latest_time = mod_time
                        latest_file = pdf_file
                except Exception as e:
                    st.warning(f"ファイル情報の取得に失敗しました ({pdf_file.name}): {e}")
                    continue
    except Exception as e:
        st.error(f"ファイル検索中にエラーが発生しました ({folder_path}): {e}")
        return None

    if not latest_file:
        pass
    return latest_file


def get_pdf_files_in_folder(folder_path: Path):
    """指定フォルダ内のPDFファイル名のリストを返す（フルパスも保持）"""
    if not folder_path.exists() or not folder_path.is_dir():
        st.warning(f"フォルダが見つかりません: {folder_path}")
        return {}

    pdf_files_dict = {}
    try:
        for pdf_file in list(folder_path.glob("*.pdf")) + list(folder_path.glob("*.PDF")):
            if pdf_file.is_file() and pdf_file.name not in pdf_files_dict:
                pdf_files_dict[pdf_file.name] = pdf_file
    except Exception as e:
        st.error(f"フォルダ内のPDFリスト取得中にエラーが発生しました ({folder_path}): {e}")
    return pdf_files_dict


# --- メイン処理 ---
root_dir = Path(ROOT_DIR_PATH_STR)

if not root_dir.exists() or not root_dir.is_dir():
    st.error(f"指定されたルートフォルダが見つかりません。パスを確認してください: {ROOT_DIR_PATH_STR}")
    st.stop()

tabs = st.tabs(TAB_NAMES_FOR_DISPLAY)  # 表示用のタブ名リストを使用

for i, tab_name_for_display in enumerate(TAB_NAMES_FOR_DISPLAY):
    actual_tab_name = TAB_NAMES_FOR_LOGIC[i]

    with tabs[i]:
        if actual_tab_name == "発行台帳":
            latest_pdf = find_latest_pdf_with_keyword(root_dir, "発行台帳")
            if latest_pdf:
                display_pdf(latest_pdf)
            else:
                st.info(f"「発行台帳」関連のPDFファイルが見つかりませんでした。")

        elif actual_tab_name == "配布票":
            latest_pdf = find_latest_pdf_with_keyword(root_dir, "配布票")
            if latest_pdf:
                display_pdf(latest_pdf)
            else:
                st.info(f"「配布票」関連のPDFファイルが見つかりませんでした。")

        elif actual_tab_name in ["EA", "EC", "EG", "EI", "EK", "EM", "ES", "EW"]:
            model_specific_folder_parent = root_dir / KIJUN_CHECK_HYO_PARENT_FOLDER_NAME
            model_folder = model_specific_folder_parent / actual_tab_name

            if not model_specific_folder_parent.exists() or not model_specific_folder_parent.is_dir():
                st.error(
                    f"基準チェック表の親フォルダ「{KIJUN_CHECK_HYO_PARENT_FOLDER_NAME}」が見つかりません。")
                continue

            if not model_folder.exists() or not model_folder.is_dir():
                st.warning(
                    f"機種別フォルダ「{actual_tab_name}」が見つかりません: {model_folder}")
                st.info(f"機種「{actual_tab_name}」のPDFフォルダが見つかりません。")
                continue

            pdf_files_map = get_pdf_files_in_folder(model_folder)

            if pdf_files_map:
                sorted_pdf_names = sorted(pdf_files_map.keys())
                session_key = f"selected_pdf_{actual_tab_name}"
                current_selection_index = 0
                if session_key in st.session_state and st.session_state[session_key] in sorted_pdf_names:
                    current_selection_index = sorted_pdf_names.index(
                        st.session_state[session_key])
                elif sorted_pdf_names:
                    st.session_state[session_key] = sorted_pdf_names[0]

                selected_pdf_name = st.selectbox(
                    f"{actual_tab_name} - PDFファイルを選択してください:",
                    options=sorted_pdf_names,
                    key=session_key,
                    index=current_selection_index,
                    disabled=not sorted_pdf_names
                )

                if selected_pdf_name:
                    selected_pdf_path = pdf_files_map[selected_pdf_name]
                    display_pdf(selected_pdf_path)
            else:
                st.info(
                    f"機種「{actual_tab_name}」のフォルダ ({model_folder.name}) には表示できるPDFファイルがありません。")
        else:
            st.error(
                f"不明なタブ処理です: 表示名「{tab_name_for_display}」、処理名「{actual_tab_name}」")

st.markdown("---")
st.caption(f"ルートフォルダ: {ROOT_DIR_PATH_STR}")
