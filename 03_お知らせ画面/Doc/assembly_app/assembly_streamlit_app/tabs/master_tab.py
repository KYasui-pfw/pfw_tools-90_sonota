###
# アッセンブリー課チェックシート
# Start 20250625 ダイヤルキャップとホルダーを開始
# ADD_20250626 ギアボックス追加
###
import streamlit as st
import database


def render():
    """マスター管理タブのUIを描画する"""

    # [修正] 管理対象のリストを関数の最初に定義し、「ギアボックスGr」を追加
    checksheet_names = ["ダイヤルキャップ", "ホルダー", "ギアボックスGr", "シンカーキャップ"]

    col1, col2, _ = st.columns(3)

    # --- 作業者・確認者マスター管理 ---
    with col1:
        st.subheader("作業者・確認者マスター管理")

        worker_selected_checksheet = st.selectbox(
            "対象のチェックシートを選択してください",
            options=checksheet_names,
            key="worker_master_select"
        )

        if worker_selected_checksheet:
            # st.data_editorの状態をセッションで保持するためのキー
            editor_key = f"worker_editor_{worker_selected_checksheet}"

            # セッションにデータがなければDBから読み込む
            if editor_key not in st.session_state:
                st.session_state[editor_key] = database.get_workers_for_checksheet(
                    worker_selected_checksheet)

            # データエディタを表示
            edited_worker_df = st.data_editor(
                st.session_state[editor_key],
                num_rows="dynamic",
                key=f"w_editor_{worker_selected_checksheet}",
                use_container_width=True,
                column_config={
                    "worker_name": "作業者・確認者名",
                    "display_order": st.column_config.NumberColumn("表示順", help="数値が小さいほど先に表示されます。", format="%d")
                },
                column_order=("display_order", "worker_name")
            )

            # 更新ボタンが押されたら、DB同期関数を呼び出す
            if st.button(f"作業者リストを更新", key=f"update_master_w_{worker_selected_checksheet}"):
                try:
                    database.sync_worker_master(
                        worker_selected_checksheet, edited_worker_df.dropna(subset=['worker_name']))
                    st.success(
                        f"「{worker_selected_checksheet}」の作業者リストを更新しました。")
                    # 成功したらセッションキャッシュを削除して再読み込み
                    del st.session_state[editor_key]
                    st.rerun()
                except ValueError as e:
                    st.error(e)
                except Exception as e:
                    st.error(f"作業者マスター更新中にエラー: {e}")

    # --- 計測器マスター管理 ---
    with col2:
        st.subheader("計測器マスター管理")

        inst_selected_checksheet = st.selectbox(
            "対象のチェックシートを選択してください",
            options=checksheet_names,
            key="inst_master_select"
        )

        if inst_selected_checksheet:
            # st.data_editorの状態をセッションで保持するためのキー
            inst_editor_key = f"instrument_editor_{inst_selected_checksheet}"

            # セッションにデータがなければDBから読み込む
            if inst_editor_key not in st.session_state:
                st.session_state[inst_editor_key] = database.get_instruments_for_checksheet(
                    inst_selected_checksheet)

            # データエディタを表示
            edited_instrument_df = st.data_editor(
                st.session_state[inst_editor_key],
                num_rows="dynamic",
                key=f"i_editor_{inst_selected_checksheet}",
                use_container_width=True,
                column_config={
                    "instrument_no": "計測器No",
                    "display_order": st.column_config.NumberColumn("表示順", help="数値が小さいほど先に表示されます。", format="%d")
                },
                column_order=("display_order", "instrument_no")
            )

            # 更新ボタンが押されたら、DB同期関数を呼び出す
            if st.button("計測器リストを更新", key=f"update_master_i_{inst_selected_checksheet}"):
                try:
                    database.sync_instrument_master(
                        inst_selected_checksheet, edited_instrument_df.dropna(subset=['instrument_no']))
                    st.success(f"「{inst_selected_checksheet}」の計測器リストを更新しました。")
                    # 成功したらセッションキャッシュを削除して再読み込み
                    del st.session_state[inst_editor_key]
                    st.rerun()
                except ValueError as e:
                    st.error(e)
                except Exception as e:
                    st.error(f"計測器マスター更新中にエラー: {e}")
