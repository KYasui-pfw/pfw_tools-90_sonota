# streamlit_app/main.py

import streamlit as st
import sys
import requests
import time
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db_manager import DatabaseManager
from app.config import config

# ページ設定
st.set_page_config(
    page_title="rBOMメール通知管理",
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

st.title("📧 rBOMメール通知管理画面")

# 画面起動時に自動で社員マスタを同期
if 'synced' not in st.session_state:
    with st.spinner("社員マスタを同期中..."):
        employees = fetch_employees_from_api()
        if employees:
            count = db.sync_employee_master(employees)
            st.session_state.synced = True
            st.toast(f"社員マスタを同期しました（{count}件）", icon="✅")

# タブで機能を分割
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚠️ エラーメール送信先設定",
    "🔧 経費工具受入メール送信先設定",
    "📜 エラーメール送信履歴",
    "📋 経費工具受入メール送信履歴",
    "📖 使い方"
])

# ========== タブ1: エラーメール送信先設定 ==========
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
        # 初期値用に空の選択肢を追加
        employee_options_with_default = {"": None}
        employee_options_with_default.update(employee_options)

        col1, col_space, col2, col3, col4 = st.columns([2, 1, 1, 1, 1])
        with col1:
            # session_stateで選択状態を保持
            if 'error_selected_label' not in st.session_state:
                st.session_state.error_selected_label = ""

            # 現在の選択状態からindexを取得
            current_index = 0
            if st.session_state.error_selected_label in employee_options_with_default:
                current_index = list(employee_options_with_default.keys()).index(st.session_state.error_selected_label)

            selected_label = st.selectbox(
                "送信先を設定する社員を選択（入力で検索可能）",
                list(employee_options_with_default.keys()),
                index=current_index,
                key="error_selectbox"
            )

            # 選択状態を保存
            st.session_state.error_selected_label = selected_label

        selected_tancd = employee_options_with_default[selected_label]

        # 社員が選択されている場合のみ以降を表示
        if selected_tancd is None:
            st.info("👆 社員を選択してください")
        else:
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
                        subcol1, subcol2 = st.columns(2)
                        with subcol1:
                            st.write("")  # ラベル分の空白
                            submitted_acceptance = st.form_submit_button("受入設定を保存", type="primary")

                    if submitted_acceptance:
                        try:
                            db.bulk_update_recipients(selected_tancd, "acceptance", "TO", acceptance_to)
                            db.bulk_update_recipients(selected_tancd, "acceptance", "CC", acceptance_cc)
                            with subcol2:
                                st.write("")  # ラベル分の空白
                                st.success("登録完了")
                            time.sleep(3)
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
                        subcol1, subcol2 = st.columns(2)
                        with subcol1:
                            st.write("")  # ラベル分の空白
                            submitted_picking = st.form_submit_button("棚出設定を保存", type="primary")

                    if submitted_picking:
                        try:
                            db.bulk_update_recipients(selected_tancd, "picking", "TO", picking_to)
                            db.bulk_update_recipients(selected_tancd, "picking", "CC", picking_cc)
                            with subcol2:
                                st.write("")  # ラベル分の空白
                                st.success("登録完了")
                            time.sleep(3)
                            st.rerun()
                        except Exception as e:
                            st.error(f"保存に失敗しました: {e}")

# ========== タブ2: 経費工具受入メール送信先設定 ==========
with tab2:
    # 社員一覧を取得（有効な社員のみ）
    employees = db.get_all_employees(include_inactive=False)

    # 例外処理: 社員コードが#または*の1文字のみの場合は除外
    employees = [emp for emp in employees if emp['tancd'] not in ['#', '*']]

    if not employees:
        st.warning("社員データがありません。")
    else:
        # 社員選択と社員情報を横並びで表示
        employee_options = {f"{emp['tancd']} - {emp['tannm']}": emp['tancd'] for emp in employees}
        # 初期値用に空の選択肢を追加
        employee_options_with_default = {"": None}
        employee_options_with_default.update(employee_options)

        col1, col_space, col2, col3, col4 = st.columns([2, 1, 1, 1, 1])
        with col1:
            # session_stateで選択状態を保持
            if 'expense_selected_label' not in st.session_state:
                st.session_state.expense_selected_label = ""

            # 現在の選択状態からindexを取得
            current_index = 0
            if st.session_state.expense_selected_label in employee_options_with_default:
                current_index = list(employee_options_with_default.keys()).index(st.session_state.expense_selected_label)

            selected_label = st.selectbox(
                "送信先を設定する社員を選択（入力で検索可能）",
                list(employee_options_with_default.keys()),
                index=current_index,
                key="expense_tool_selectbox"
            )

            # 選択状態を保存
            st.session_state.expense_selected_label = selected_label

        selected_tancd = employee_options_with_default[selected_label]

        # 社員が選択されている場合のみ以降を表示
        if selected_tancd is None:
            st.info("👆 社員を選択してください")
        else:
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

            # 現在の設定を取得
            current_recipients = db.get_all_recipients_by_tancd(selected_tancd)

            # 経費工具受入機能の設定フォーム
            with st.form(f"expense_tool_form_{selected_tancd}"):
                st.write("**経費工具受入TO（宛先）**")
                expense_tool_to = []

                # TO 1行目（3個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2, col3]):
                    with col:
                        default_val = current_recipients["expense_tool"]["TO"][i] if i < len(current_recipients["expense_tool"]["TO"]) else ""
                        email = st.text_input(f"TO {i+1}", value=default_val, key=f"exp_to_{i}", max_chars=255, label_visibility="visible")
                        expense_tool_to.append(email)

                # TO 2行目（2個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2], start=3):
                    with col:
                        default_val = current_recipients["expense_tool"]["TO"][i] if i < len(current_recipients["expense_tool"]["TO"]) else ""
                        email = st.text_input(f"TO {i+1}", value=default_val, key=f"exp_to_{i}", max_chars=255, label_visibility="visible")
                        expense_tool_to.append(email)

                st.write("**経費工具受入CC（CC）**")
                expense_tool_cc = []

                # CC 1行目（3個）
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2, col3]):
                    with col:
                        default_val = current_recipients["expense_tool"]["CC"][i] if i < len(current_recipients["expense_tool"]["CC"]) else ""
                        email = st.text_input(f"CC {i+1}", value=default_val, key=f"exp_cc_{i}", max_chars=255, label_visibility="visible")
                        expense_tool_cc.append(email)

                # CC 2行目（2個）+ 保存ボタン
                col1, col2, col3 = st.columns(3)
                for i, col in enumerate([col1, col2], start=3):
                    with col:
                        default_val = current_recipients["expense_tool"]["CC"][i] if i < len(current_recipients["expense_tool"]["CC"]) else ""
                        email = st.text_input(f"CC {i+1}", value=default_val, key=f"exp_cc_{i}", max_chars=255, label_visibility="visible")
                        expense_tool_cc.append(email)

                with col3:
                    st.write("")  # ラベル分の空白
                    subcol1, subcol2 = st.columns(2)
                    with subcol1:
                        st.write("")  # ラベル分の空白
                        submitted_expense_tool = st.form_submit_button("経費工具受入設定を保存", type="primary")

                if submitted_expense_tool:
                    try:
                        db.bulk_update_recipients(selected_tancd, "expense_tool", "TO", expense_tool_to)
                        db.bulk_update_recipients(selected_tancd, "expense_tool", "CC", expense_tool_cc)
                        with subcol2:
                            st.write("")  # ラベル分の空白
                            st.success("登録完了")
                        time.sleep(3)
                        st.rerun()
                    except Exception as e:
                        st.error(f"保存に失敗しました: {e}")

# ========== タブ3: エラーメール送信履歴 ==========
with tab3:
    st.header("エラーメール送信履歴（30日分）")

    all_histories = db.get_mail_history(days=30)

    # エラーメールのみをフィルタ（受入機能・棚出機能）
    histories = [h for h in all_histories if h.get('function_name') in ['受入機能', '棚出機能']]

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

# ========== タブ4: 経費工具受入メール送信履歴 ==========
with tab4:
    st.header("経費工具受入メール送信履歴（30日分）")

    all_histories = db.get_mail_history(days=30)

    # 経費工具受入メールのみをフィルタ
    histories = [h for h in all_histories if h.get('function_name') == '経費工具受入機能']

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

# ========== タブ5: 使い方 ==========
with tab5:
    st.markdown("""
    ## システム概要
    このツールは、rBOMの連携用テーブルを監視し、以下の2つの機能でメール通知を送信する仕組みです：

    1. **エラーメール通知**: 実績登録でエラーが発生した際に担当者へ自動でメール通知
    2. **経費工具受入メール通知**: 経費工具の受入時に担当者へメール通知（条件は別途設定）

    ## 使い方
    - 「エラーメール送信先設定」または「経費工具受入メール送信先設定」のタブで社員を選択します。
    - ToやCCのメール送信先を登録すると、該当するイベント発生時に対象者にメールを送信します。
    - メール送信先の登録がなくても運用上問題はありませんが、通知は送信されません。

    ---

    ## システム詳細
    """)

    st.write("")  # 空行を追加

    st.markdown("""
    ### 💡 メール送信先設定タブ

    #### 1. 社員の選択
    - プルダウンから社員を選択してください
    - **検索機能**: プルダウン内で文字を入力すると、該当する社員が絞り込まれます
    - 例: 「福原」と入力すると「福原太郎」が表示されます

    #### 2. 送信先の設定
    - **受入機能** と **棚出機能** の2つの機能ごとに設定できます
    - 各機能で **TO（宛先）** と **CC** をそれぞれ最大5件まで登録可能

    #### 3. メールアドレスの入力
    - 会社のメールアドレス（例: `taro.fukuhara@pfw.co.jp`）を入力してください
    - 空欄のままでもOKです（使用しない場合）

    #### 4. 保存
    - 「受入設定を保存」または「棚出設定を保存」ボタンをクリックすると設定が保存されます

    ---

    ### 📬 メール送信の仕組み

    #### エラー検知
    システムは**5分ごと**に以下のテーブルを監視しています：
    - **DK020**: 受入実績データ
    - **DK040**: 棚出実績データ

    #### 送信条件
    - エラーステータス（`SYORIZUMIKBN = '3'`）のレコードを検知
    - 登録した担当者（`IPTANCD`）に対応するメールアドレスに通知

    #### 送信内容
    メールには以下の情報が含まれます：
    - 機能名（受入 or 棚出）
    - 発注番号/引当番号
    - 行番号
    - リスト番号
    - 品目コード・品目名
    - 登録日時
    - 担当者コード・担当者名

    #### 重複送信防止
    - 同じエラーには**1回のみ**メール送信されます
    - 送信履歴はデータベースに記録されます

    ---

    ### 📜 メール送信履歴タブ

    #### 表示内容
    - 過去**30日間**のメール送信履歴を表示
    - 送信日時、機能、発注/引当番号、品目情報、送信先などが確認できます

    #### データの見方
    - **送信先**: `to:メールアドレス, cc:メールアドレス` 形式で表示
    - **テーブル**: エラーが発生した元のテーブル（DK020 or DK040）

    ---

    ### ⚠️ 注意事項

    #### 社員マスタの同期
    - 画面起動時に自動で社員マスタ（M0540）と同期されます
    - 新しい社員が追加された場合は、画面を再読み込みしてください

    #### メールアドレスの正確性
    - 間違ったメールアドレスを登録すると、エラー通知が届きません
    - 設定後は必ず確認してください

    #### 送信タイミング
    - メール送信は**5分間隔**で実行されます
    - エラー発生から最大5分程度の遅延が発生する可能性があります

    ---

    ### 🆘 トラブルシューティング

    #### メールが届かない場合
    1. メールアドレスが正しく登録されているか確認
    2. 迷惑メールフォルダを確認
    3. 送信履歴タブで送信記録を確認

    #### 設定が保存できない場合
    1. メールアドレスの形式が正しいか確認（`@pfw.co.jp` が含まれているか）
    2. ブラウザを再読み込みして再度試行

    #### 社員が表示されない場合
    1. 画面を再読み込みして社員マスタを再同期
    2. M0540テーブルに該当社員が登録されているか確認
    """)
