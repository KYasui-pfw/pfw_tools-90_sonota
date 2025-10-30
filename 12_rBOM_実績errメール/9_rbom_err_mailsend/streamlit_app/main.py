# streamlit_app/main.py

import streamlit as st
import sys
import requests
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db_manager import DatabaseManager
from app.config import config

# ページ設定
st.set_page_config(
    page_title="rBOM エラー通知メール管理",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ヘッダー行を非表示にし、上部余白を削減
st.markdown("""
<style>
    /* ヘッダーとフッターを非表示 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* 上部の余白を削減 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }

    /* タイトルの余白を削減 */
    h1 {
        margin-top: 0;
        padding-top: 0;
    }

    /* 保存ボタンを赤色に */
    button[kind="primary"] {
        background-color: #ff4b4b !important;
        border-color: #ff4b4b !important;
    }
    button[kind="primary"]:hover {
        background-color: #ff3333 !important;
        border-color: #ff3333 !important;
    }
</style>
""", unsafe_allow_html=True)

# データベースマネージャーを初期化
@st.cache_resource
def get_db_manager():
    return DatabaseManager()

db = get_db_manager()


def fetch_employees_from_api():
    """FastAPI経由でM0540（社員マスタ）を取得"""
    try:
        api_url = f"{config.FASTAPI_BASE_URL}/query"
        headers = {"X-API-KEY": config.READ_API_KEY}
        payload = {
            "table": "M0540",
            "columns": ["TANCD", "TANNM", "VALFLG"]
        }

        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("rows", [])
    except Exception as e:
        st.error(f"社員マスタの取得に失敗しました: {e}")
        return []


def sync_employee_master():
    """M0540から社員マスタを同期"""
    with st.spinner("社員マスタを同期中..."):
        employees = fetch_employees_from_api()
        if employees:
            count = db.sync_employee_master(employees)
            st.success(f"社員マスタを同期しました（{count}件）")
            st.rerun()
        else:
            st.warning("同期するデータがありません")


# ========== メインページ ==========

st.title("📧 rBOM エラー通知メール管理画面")

# 画面起動時に自動で社員マスタを同期
if 'synced' not in st.session_state:
    with st.spinner("社員マスタを同期中..."):
        employees = fetch_employees_from_api()
        if employees:
            count = db.sync_employee_master(employees)
            st.session_state.synced = True
            st.toast(f"社員マスタを同期しました（{count}件）", icon="✅")

# タブで機能を分割
tab1, tab2 = st.tabs(["👤 メール送信先設定", "📜 メール送信履歴"])

# ========== タブ1: メール送信先設定 ==========
with tab1:
    # 社員一覧を取得（有効な社員のみ）
    employees = db.get_all_employees(include_inactive=False)

    # 例外処理: 社員コードが#または*の1文字のみの場合は除外
    employees = [emp for emp in employees if emp['tancd'] not in ['#', '*']]

    if not employees:
        st.warning("社員データがありません。")
    else:
        # 社員選択と社員情報を横並びで表示
        employee_options = {f"{emp['tancd']} - {emp['tannm']}": emp['tancd'] for emp in employees}

        col1, col_space, col2, col3, col4 = st.columns([2, 1, 1, 1, 1])
        with col1:
            selected_label = st.selectbox("送信先を設定する社員を選択", list(employee_options.keys()))

        selected_tancd = employee_options[selected_label]
        employee = db.get_employee_by_tancd(selected_tancd)

        with col2:
            st.markdown("**社員コード**")
            st.write(employee['tancd'])
        with col3:
            st.markdown("**社員名**")
            st.write(employee['tannm'])
        with col4:
            st.markdown("**ステータス**")
            status = "✅ 有効" if employee['valflg'] == '1' else "❌ 無効"
            st.write(status)

        #st.markdown("---")

        # 現在の設定を取得
        current_recipients = db.get_all_recipients_by_tancd(selected_tancd)

        # 受入機能と棚出機能をタブで切り替え
        func_tab1, func_tab2 = st.tabs(["受入機能", "棚出機能"])

        # ========== 受入機能タブ ==========
        with func_tab1:
            with st.form(f"acceptance_form_{selected_tancd}"):
                st.write("**受入TO（宛先）**")
                acceptance_to = []

                # TO 1行目（3個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2, col3]):
                    with col:
                        default_val = current_recipients["acceptance"]["TO"][i] if i < len(current_recipients["acceptance"]["TO"]) else ""
                        email = st.text_input(f"TO {i+1}", value=default_val, key=f"acc_to_{i}", max_chars=255, label_visibility="visible")
                        acceptance_to.append(email)

                # TO 2行目（2個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2], start=3):
                    with col:
                        default_val = current_recipients["acceptance"]["TO"][i] if i < len(current_recipients["acceptance"]["TO"]) else ""
                        email = st.text_input(f"TO {i+1}", value=default_val, key=f"acc_to_{i}", max_chars=255, label_visibility="visible")
                        acceptance_to.append(email)

                st.write("**受入CC（CC）**")
                acceptance_cc = []

                # CC 1行目（3個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2, col3]):
                    with col:
                        default_val = current_recipients["acceptance"]["CC"][i] if i < len(current_recipients["acceptance"]["CC"]) else ""
                        email = st.text_input(f"CC {i+1}", value=default_val, key=f"acc_cc_{i}", max_chars=255, label_visibility="visible")
                        acceptance_cc.append(email)

                # CC 2行目（2個）+ 保存ボタン
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2], start=3):
                    with col:
                        default_val = current_recipients["acceptance"]["CC"][i] if i < len(current_recipients["acceptance"]["CC"]) else ""
                        email = st.text_input(f"CC {i+1}", value=default_val, key=f"acc_cc_{i}", max_chars=255, label_visibility="visible")
                        acceptance_cc.append(email)

                with col3:
                    st.write("")  # ラベル分の空白
                    submitted_acceptance = st.form_submit_button("受入設定を保存", type="primary")

                if submitted_acceptance:
                    try:
                        db.bulk_update_recipients(selected_tancd, "acceptance", "TO", acceptance_to)
                        db.bulk_update_recipients(selected_tancd, "acceptance", "CC", acceptance_cc)
                        st.success("受入機能の設定を保存しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"保存に失敗しました: {e}")

        # ========== 棚出機能タブ ==========
        with func_tab2:
            with st.form(f"picking_form_{selected_tancd}"):
                st.write("**棚出TO（宛先）**")
                picking_to = []

                # TO 1行目（3個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2, col3]):
                    with col:
                        default_val = current_recipients["picking"]["TO"][i] if i < len(current_recipients["picking"]["TO"]) else ""
                        email = st.text_input(f"TO {i+1}", value=default_val, key=f"pick_to_{i}", max_chars=255, label_visibility="visible")
                        picking_to.append(email)

                # TO 2行目（2個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2], start=3):
                    with col:
                        default_val = current_recipients["picking"]["TO"][i] if i < len(current_recipients["picking"]["TO"]) else ""
                        email = st.text_input(f"TO {i+1}", value=default_val, key=f"pick_to_{i}", max_chars=255, label_visibility="visible")
                        picking_to.append(email)

                st.write("**棚出CC（CC）**")
                picking_cc = []

                # CC 1行目（3個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2, col3]):
                    with col:
                        default_val = current_recipients["picking"]["CC"][i] if i < len(current_recipients["picking"]["CC"]) else ""
                        email = st.text_input(f"CC {i+1}", value=default_val, key=f"pick_cc_{i}", max_chars=255, label_visibility="visible")
                        picking_cc.append(email)

                # CC 2行目（2個）+ 保存ボタン
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2], start=3):
                    with col:
                        default_val = current_recipients["picking"]["CC"][i] if i < len(current_recipients["picking"]["CC"]) else ""
                        email = st.text_input(f"CC {i+1}", value=default_val, key=f"pick_cc_{i}", max_chars=255, label_visibility="visible")
                        picking_cc.append(email)

                with col3:
                    st.write("")  # ラベル分の空白
                    submitted_picking = st.form_submit_button("棚出設定を保存", type="primary")

                if submitted_picking:
                    try:
                        db.bulk_update_recipients(selected_tancd, "picking", "TO", picking_to)
                        db.bulk_update_recipients(selected_tancd, "picking", "CC", picking_cc)
                        st.success("棚出機能の設定を保存しました")
                        st.rerun()
                    except Exception as e:
                        st.error(f"保存に失敗しました: {e}")

# ========== タブ2: メール送信履歴 ==========
with tab2:
    st.header("メール送信履歴（30日分）")

    histories = db.get_mail_history(days=30)

    if not histories:
        st.info("送信履歴はありません（30日以内）")
    else:
        st.write(f"**送信履歴: {len(histories)}件（過去30日分）**")

        # pandasデータフレーム用にカラム名を整形
        import pandas as pd

        df_data = []
        for h in histories:
            df_data.append({
                "送信日時": h.get('sent_at', '-'),
                "機能": h.get('function_name', '-'),
                "発注/引当番号": h.get('order_no', '-'),
                "行番号": h.get('line_no', '-'),
                "リスト番号": h.get('listno', '-'),
                "品目コード": h.get('hmcd', '-'),
                "品目名": h.get('hmnm', '-'),
                "登録日時": h.get('instdt', '-'),
                "社員コード": h.get('employee_code', '-'),
                "社員名": h.get('employee_name', '-'),
                "送信先": h.get('email_addresses', '-'),
                "テーブル": h.get('table_name', '-')
            })

        df = pd.DataFrame(df_data)

        # データフレームを表示（幅を最大化）
        st.dataframe(
            df,
            use_container_width=True,
            height=600,
            hide_index=True
        )

