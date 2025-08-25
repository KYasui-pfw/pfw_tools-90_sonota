###
# アッセンブリー課チェックシート
# Start 20250625 ダイヤルキャップとホルダーを開始
# ADD_20250626 ギアボックス追加
###
import streamlit as st


def initialize_session_state():
    """
    アプリケーション全体で使用するセッション変数を初期化する。

    この関数はアプリケーションの起動時に一度だけ呼び出され、
    各チェックシートが使用する状態管理用のキーを
    あらかじめ定義しておくことで、KeyErrorの発生を防ぎます。
    """

    # 将来的にチェックシートの種類が増えても、このリストに追加するだけで対応可能
    checksheet_prefixes = ['dial_cap_', 'holder_',
                           'gearbox_gr_', 'sinker_cap_']  # 「gearbox_gr_」を追加

    for prefix in checksheet_prefixes:
        # 更新処理中フラグ、削除確認中フラグ、追加処理メッセージ
        for key_suffix in ['update_in_progress', 'confirming_deletion', 'add_message']:
            key = f"{prefix}{key_suffix}"
            if key not in st.session_state:
                # フラグはFalse、メッセージは空文字列で初期化
                is_flag = 'in_progress' in key_suffix or 'deletion' in key_suffix
                st.session_state[key] = False if is_flag else ""

        # 最後にデータを取得した年月
        if f"{prefix}last_fetched_year_month" not in st.session_state:
            st.session_state[f"{prefix}last_fetched_year_month"] = (None, None)

        # 手動追加用の入力フィールドの状態
        if f"{prefix}new_machine_no" not in st.session_state:
            st.session_state[f"{prefix}new_machine_no"] = ""
        if f"{prefix}new_model_name" not in st.session_state:
            st.session_state[f"{prefix}new_model_name"] = ""
        if f"{prefix}new_size_inch" not in st.session_state:
            st.session_state[f"{prefix}new_size_inch"] = ""
        if f"{prefix}new_gauge" not in st.session_state:
            st.session_state[f"{prefix}new_gauge"] = ""
        if f"{prefix}new_suffix" not in st.session_state:
            st.session_state[f"{prefix}new_suffix"] = 1

    # AgGridの再描画を強制するためのカウンター
    if 'session_count' not in st.session_state:
        st.session_state['session_count'] = 0
