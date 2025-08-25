import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import pytz

st.set_page_config(
    page_title="お知らせ掲示板",
    page_icon="📢",
    layout="wide"
)

# ヘッダー部を完全に削除
st.markdown("""
<style>
    .block-container {
        padding-top: 0rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .main .block-container {
        max-width: none;
    }
    /* Streamlitのヘッダーを完全に非表示 */
    header[data-testid="stHeader"] {
        display: none;
    }
    /* メニューボタンを非表示 */
    .css-1rs6os.edgvbvh3 {
        display: none;
    }
    /* Deploy等のボタンを非表示 */
    .css-14xtw13.e8zbici0 {
        display: none;
    }
    /* オレンジ色の線を非表示 */
    .css-1d391kg {
        display: none;
    }
    /* 上部のグラデーション線を非表示 */
    .stApp > header {
        display: none;
    }
    .stApp > div[data-testid="stDecoration"] {
        display: none;
    }
    /* タイトルの余白調整 */
    h1 {
        padding-top: 0rem;
        margin-top: 0rem;
    }
</style>
""", unsafe_allow_html=True)

DATABASE_PATH = "notices.db"

def auto_delete_expired_notices():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    thirty_days_ago = datetime.now() - timedelta(days=30)
    cursor.execute('''
        UPDATE notices 
        SET deleted_at = CURRENT_TIMESTAMP 
        WHERE end_date < ? AND deleted_at IS NULL
    ''', (thirty_days_ago.date(),))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count

def get_active_notices():
    conn = sqlite3.connect(DATABASE_PATH)
    # 終了日が今日に近い順（昇順）でソート
    # end_date >= todayにより、終了日翌日から自動的に非表示になる
    today = datetime.now().date()
    df = pd.read_sql_query('''
        SELECT * FROM notices 
        WHERE deleted_at IS NULL 
        AND start_date <= ? 
        AND end_date >= ?
        ORDER BY end_date ASC, start_date ASC
    ''', conn, params=(today, today))
    conn.close()
    return df

@st.dialog("お知らせ詳細")
def show_notice_dialog(notice):
    """お知らせの詳細をモーダルダイアログで表示"""
    emoji_display = notice.get('emoji', '📋')
    
    # 日付をmm/dd形式に変換
    from datetime import datetime
    start_date = datetime.strptime(notice['start_date'], '%Y-%m-%d').strftime('%m/%d')
    end_date = datetime.strptime(notice['end_date'], '%Y-%m-%d').strftime('%m/%d')
    
    # ヘッダー情報
    st.markdown(f"### {emoji_display} {notice['title']}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**部門:** {notice['department']}")
    with col2:
        st.write(f"**掲載期間:** {start_date} ～ {end_date}")
    
    st.write("---")
    
    # 本文
    formatted_content = notice['content'].replace('\n', '  \n')
    st.markdown(formatted_content, unsafe_allow_html=True)
    
    st.write("---")
    # 作成日時
    st.write(f"**作成日時:** {notice['created_at']}")

def display_notice_card(notice):
    """お知らせカードを表示する関数"""
    emoji_display = notice.get('emoji', '📋')
    
    # 日付をmm/dd形式に変換
    from datetime import datetime
    start_date = datetime.strptime(notice['start_date'], '%Y-%m-%d').strftime('%m/%d')
    end_date = datetime.strptime(notice['end_date'], '%Y-%m-%d').strftime('%m/%d')
    
    # クリック可能なカード表示
    if st.button(
        f"{emoji_display} {notice['title']}\n({notice['department']}) | {start_date} ～ {end_date}",
        key=f"notice_{notice['id']}",
        use_container_width=True
    ):
        show_notice_dialog(notice)

def main():
    # 自動削除実行
    auto_delete_expired_notices()
    
    # アクティブなお知らせを取得
    notices_df = get_active_notices()
    
    if notices_df.empty:
        st.info("📝 現在表示中のお知らせはありません。")
        return
    
    
    notices_list = notices_df.to_dict('records')
    

    st.write("【お知らせ】")
    for notice in notices_list:
        display_notice_card(notice)

if __name__ == "__main__":
    main()
