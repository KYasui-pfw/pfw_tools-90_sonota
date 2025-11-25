"""
マッピング結果表示ページ

ロット番号とINDNOのマッピング結果を表示
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# database.pyをインポートするためにパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DatabaseManager
from sqlalchemy import text


st.set_page_config(
    page_title="マッピング結果",
    page_icon="🔗",
    layout="wide"
)

st.title("🔗 マッピング結果")
st.markdown("---")


def main():
    """メイン処理"""

    db_manager = DatabaseManager()

    # テーブルの初期化（存在しない場合のみ作成）
    db_manager._initialize_sqlite_table()

    try:
        engine = db_manager._connect_sqlite()

        # マッピング結果取得
        query = text("""
        SELECT
            id,
            lot_number AS ロット番号,
            indno AS 指示番号,
            item_code AS 品目コード,
            assembly_number AS 組立番号,
            hmcd AS HMCD,
            seino AS SEINO,
            mapping_type AS マッピング種別,
            created_at AS 登録日時
        FROM mapping_results
        ORDER BY created_at DESC
        """)

        df = pd.read_sql(query, engine)

        if df.empty:
            st.warning("⚠️ マッピング結果がありません。まずはメインページでデータを取得してください。")
        else:
            # 統計情報
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("総マッピング数", f"{len(df):,}")

            with col2:
                auto_count = len(df[df['マッピング種別'] == 'auto'])
                st.metric("自動マッピング", f"{auto_count:,}")

            with col3:
                manual_count = len(df[df['マッピング種別'] == 'manual'])
                st.metric("手動マッピング", f"{manual_count:,}")

            with col4:
                unique_lots = df['ロット番号'].nunique()
                st.metric("ユニークロット数", f"{unique_lots:,}")

            # フィルター機能
            st.markdown("---")
            st.subheader("🔍 フィルター")

            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                # マッピング種別フィルター
                mapping_types = ['全て', 'auto', 'manual']
                selected_type = st.selectbox("マッピング種別", mapping_types)

            with filter_col2:
                # ロット番号検索
                search_lot = st.text_input("ロット番号検索", "")

            with filter_col3:
                # 指示番号検索
                search_indno = st.text_input("指示番号検索", "")

            # フィルター適用
            filtered_df = df.copy()

            if selected_type != '全て':
                filtered_df = filtered_df[filtered_df['マッピング種別'] == selected_type]

            if search_lot:
                filtered_df = filtered_df[
                    filtered_df['ロット番号'].str.contains(search_lot, case=False, na=False)
                ]

            if search_indno:
                filtered_df = filtered_df[
                    filtered_df['指示番号'].str.contains(search_indno, case=False, na=False)
                ]

            # データフレーム表示
            st.markdown("---")
            st.write(f"**表示件数:** {len(filtered_df)}件")

            st.dataframe(
                filtered_df.drop('id', axis=1),
                use_container_width=True,
                height=600,
                hide_index=True
            )

            # CSV出力
            st.markdown("---")
            csv = filtered_df.drop('id', axis=1).to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSVダウンロード",
                data=csv,
                file_name=f"mapping_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")

    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
