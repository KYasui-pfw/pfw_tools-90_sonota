"""
ロット番号マッピングツール

PostgreSQLからデータを取得してSQLiteに保存し、一覧表示するStreamlitアプリケーション
"""

import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
from database import DatabaseManager


# ページ設定
st.set_page_config(
    page_title="ロット番号マッピングツール",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ロット番号マッピングツール")
st.markdown("---")


def main():
    """メイン処理"""

    # データベースマネージャーの初期化
    db_manager = DatabaseManager()

    # サイドバー
    st.sidebar.header("データ取得設定")
    st.sidebar.markdown("""
    このアプリケーションは、以下のデータソースからデータを取得してSQLiteに保存します：

    **PostgreSQL:**
    - **view_report_405** (汎用ランニングチェックシート)
    - **view_report_334** (ダイヤルキャップ)

    **CSVファイル:**
    - **Cyl_pfw_table_KaLstCyl_All.csv**

    対象期間: **2025年11月以降**
    """)

    # 自動データ更新
    st.info("🔄 データを自動取得中...")

    try:
        # 1. 入力データ取得・保存処理
        with st.spinner("PostgreSQL/CSVからデータを取得しています..."):
            inserted_count = db_manager.merge_and_save_data()

        # 結果表示
        if inserted_count > 0:
            st.success(f"✅ 入力データ {inserted_count} 件を追加しました")
        else:
            st.info("ℹ️ 入力データに新規データはありませんでした")

        # 2. API データ取得処理
        with st.spinner("FastAPIから指示データを取得しています..."):
            api_inserted_count = asyncio.run(db_manager.fetch_api_instructions())

        if api_inserted_count > 0:
            st.success(f"✅ API データ {api_inserted_count} 件を追加しました")
        else:
            st.info("ℹ️ API データに新規データはありませんでした")

        # 3. マッピング処理実行
        with st.spinner("マッピング処理を実行しています..."):
            mapping_result = db_manager.execute_mapping()

        st.success(f"✅ マッピング完了: 自動={mapping_result['auto']}件, 手動={mapping_result['manual']}件")

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")
        st.stop()

    # データ表示
    st.markdown("---")
    st.subheader("📋 データ一覧")

    try:
        # SQLiteから全データを取得
        df = db_manager.get_all_data()

        if df.empty:
            st.warning("データがありません")
        else:
            # 統計情報（1行目）
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("総件数", f"{len(df):,}")
            with col2:
                count_405 = len(df[df['データソース'] == 'view_report_405'])
                st.metric("view_report_405", f"{count_405:,}")
            with col3:
                count_334 = len(df[df['データソース'] == 'view_report_334'])
                st.metric("view_report_334", f"{count_334:,}")
            with col4:
                unique_lots = df['ロット番号'].nunique()
                st.metric("ユニークロット番号", f"{unique_lots:,}")

            # 統計情報（2行目）
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                count_cyl = len(df[df['データソース'] == 'Cyl_pfw_table_KaLstCyl_All'])
                st.metric("Cyl CSV", f"{count_cyl:,}")
            with col6:
                st.metric("", "")  # 空のスペース
            with col7:
                st.metric("", "")  # 空のスペース
            with col8:
                st.metric("", "")  # 空のスペース

            # フィルター機能
            st.markdown("---")
            st.subheader("🔍 フィルター")

            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                # データソースフィルター
                data_sources = ['全て'] + df['データソース'].unique().tolist()
                selected_source = st.selectbox("データソース", data_sources)

            with filter_col2:
                # 月次フィルター
                months = ['全て'] + sorted(df['月次'].unique().tolist(), reverse=True)
                selected_month = st.selectbox("月次", months)

            with filter_col3:
                # ロット番号検索
                search_lot = st.text_input("ロット番号検索", "")

            # フィルター適用
            filtered_df = df.copy()

            if selected_source != '全て':
                filtered_df = filtered_df[filtered_df['データソース'] == selected_source]

            if selected_month != '全て':
                filtered_df = filtered_df[filtered_df['月次'] == selected_month]

            if search_lot:
                filtered_df = filtered_df[
                    filtered_df['ロット番号'].str.contains(search_lot, case=False, na=False)
                ]

            # データフレーム表示
            st.markdown("---")
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=600,
                hide_index=True
            )

            # CSV出力
            st.markdown("---")
            csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSVダウンロード",
                data=csv,
                file_name=f"lot_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ データ表示エラー: {e}")

    finally:
        # データベース接続をクローズ
        db_manager.close()


if __name__ == "__main__":
    main()
