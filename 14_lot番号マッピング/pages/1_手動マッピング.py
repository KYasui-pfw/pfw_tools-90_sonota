"""
手動マッピング設定ページ

ロット番号とSEINOを手動で紐付けるページ
"""

import streamlit as st
import pandas as pd
import sys
import os

# database.pyをインポートするためにパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DatabaseManager
from sqlalchemy import text


st.set_page_config(
    page_title="手動マッピング設定",
    page_icon="✏️",
    layout="wide"
)

st.title("✏️ 手動マッピング設定")
st.markdown("---")


def main():
    """メイン処理"""

    db_manager = DatabaseManager()

    # テーブルの初期化（存在しない場合のみ作成）
    db_manager._initialize_sqlite_table()

    # 未マッピングデータの表示
    st.subheader("⚠️ 未マッピングデータ")

    try:
        engine = db_manager._connect_sqlite()

        # 未マッピングデータを取得
        unmapped_query = text("""
        SELECT DISTINCT
            l.lot_number AS ロット番号,
            l.item_code AS 品目コード,
            l.assembly_number AS 組立番号,
            l.month AS 月次,
            l.data_source AS データソース
        FROM lot_mapping_data l
        LEFT JOIN mapping_results m ON l.lot_number = m.lot_number
        WHERE m.lot_number IS NULL
        ORDER BY l.lot_number
        """)

        df_unmapped = pd.read_sql(unmapped_query, engine)

        if df_unmapped.empty:
            st.success("✅ 未マッピングデータはありません。全てのデータがマッピング済みです。")
        else:
            st.warning(f"⚠️ {len(df_unmapped)}件の未マッピングデータがあります")

            # フィルター機能
            col_filter1, col_filter2 = st.columns(2)

            with col_filter1:
                # データソースフィルター
                data_sources = ['全て'] + df_unmapped['データソース'].unique().tolist()
                selected_source = st.selectbox("データソースフィルター", data_sources, key="unmapped_source_filter")

            with col_filter2:
                # ロット番号検索
                search_unmapped = st.text_input("ロット番号検索", "", key="unmapped_search")

            # フィルター適用
            df_filtered = df_unmapped.copy()

            if selected_source != '全て':
                df_filtered = df_filtered[df_filtered['データソース'] == selected_source]

            if search_unmapped:
                df_filtered = df_filtered[
                    df_filtered['ロット番号'].str.contains(search_unmapped, case=False, na=False)
                ]

            st.write(f"**表示件数:** {len(df_filtered)}件")

            # データフレーム表示
            st.dataframe(
                df_filtered,
                use_container_width=True,
                height=300,
                hide_index=True
            )

            # CSV出力
            csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 未マッピングデータCSVダウンロード",
                data=csv,
                file_name=f"unmapped_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ 未マッピングデータ取得エラー: {e}")

    # API側未マッピングデータの表示
    st.markdown("---")
    st.subheader("⚠️ API側未マッピングデータ")

    try:
        engine = db_manager._connect_sqlite()

        # API側未マッピングデータを取得（INDNOがmapping_resultsに存在しないもの）
        api_unmapped_query = text("""
        SELECT DISTINCT
            a.indno AS 指示番号,
            a.hmcd AS 品目コード,
            a.seino AS SEINO,
            a.seino_original AS SEINO元データ,
            a.ktcd AS 工程コード
        FROM api_instructions a
        LEFT JOIN mapping_results m ON a.indno = m.indno
        WHERE m.indno IS NULL
        ORDER BY a.indno, a.seino
        """)

        df_api_unmapped = pd.read_sql(api_unmapped_query, engine)

        if df_api_unmapped.empty:
            st.success("✅ API側の未マッピングデータはありません。全ての指示番号がマッピング済みです。")
        else:
            st.warning(f"⚠️ {len(df_api_unmapped)}件のAPI側未マッピングデータがあります")

            # フィルター機能
            col_api_unmapped1, col_api_unmapped2, col_api_unmapped3 = st.columns(3)

            with col_api_unmapped1:
                # SEINO検索
                search_api_unmapped_seino = st.text_input("SEINO検索", "", key="api_unmapped_seino_search")

            with col_api_unmapped2:
                # INDNO検索
                search_api_unmapped_indno = st.text_input("指示番号検索", "", key="api_unmapped_indno_search")

            with col_api_unmapped3:
                # HMCD検索
                search_api_unmapped_hmcd = st.text_input("品目コード検索", "", key="api_unmapped_hmcd_search")

            # フィルター適用
            df_api_unmapped_filtered = df_api_unmapped.copy()

            if search_api_unmapped_seino:
                df_api_unmapped_filtered = df_api_unmapped_filtered[
                    df_api_unmapped_filtered['SEINO'].str.contains(search_api_unmapped_seino, case=False, na=False)
                ]

            if search_api_unmapped_indno:
                df_api_unmapped_filtered = df_api_unmapped_filtered[
                    df_api_unmapped_filtered['指示番号'].str.contains(search_api_unmapped_indno, case=False, na=False)
                ]

            if search_api_unmapped_hmcd:
                df_api_unmapped_filtered = df_api_unmapped_filtered[
                    df_api_unmapped_filtered['品目コード'].str.contains(search_api_unmapped_hmcd, case=False, na=False)
                ]

            st.write(f"**表示件数:** {len(df_api_unmapped_filtered)}件")

            # データフレーム表示
            st.dataframe(
                df_api_unmapped_filtered,
                use_container_width=True,
                height=300,
                hide_index=True
            )

            # CSV出力
            csv_api_unmapped = df_api_unmapped_filtered.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 API側未マッピングデータCSVダウンロード",
                data=csv_api_unmapped,
                file_name=f"api_unmapped_data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ API側未マッピングデータ取得エラー: {e}")

    # API指示データの表示（全件）
    st.markdown("---")
    st.subheader("📡 API指示データ（全件）")

    try:
        engine = db_manager._connect_sqlite()

        # API指示データを取得
        api_query = text("""
        SELECT
            indno AS 指示番号,
            hmcd AS 品目コード,
            seino AS SEINO,
            seino_original AS SEINO元データ,
            ktcd AS 工程コード,
            created_at AS 登録日時
        FROM api_instructions
        ORDER BY indno, seino
        """)

        df_api = pd.read_sql(api_query, engine)

        if df_api.empty:
            st.warning("⚠️ APIデータがありません。メインページでデータを取得してください。")
        else:
            st.info(f"ℹ️ {len(df_api)}件のAPI指示データがあります")

            # フィルター機能
            col_api1, col_api2, col_api3 = st.columns(3)

            with col_api1:
                # SEINO検索
                search_seino = st.text_input("SEINO検索", "", key="api_seino_search")

            with col_api2:
                # INDNO検索
                search_indno = st.text_input("指示番号検索", "", key="api_indno_search")

            with col_api3:
                # HMCD検索
                search_hmcd = st.text_input("品目コード検索", "", key="api_hmcd_search")

            # フィルター適用
            df_api_filtered = df_api.copy()

            if search_seino:
                df_api_filtered = df_api_filtered[
                    df_api_filtered['SEINO'].str.contains(search_seino, case=False, na=False)
                ]

            if search_indno:
                df_api_filtered = df_api_filtered[
                    df_api_filtered['指示番号'].str.contains(search_indno, case=False, na=False)
                ]

            if search_hmcd:
                df_api_filtered = df_api_filtered[
                    df_api_filtered['品目コード'].str.contains(search_hmcd, case=False, na=False)
                ]

            st.write(f"**表示件数:** {len(df_api_filtered)}件")

            # データフレーム表示
            st.dataframe(
                df_api_filtered,
                use_container_width=True,
                height=300,
                hide_index=True
            )

            # CSV出力
            csv_api = df_api_filtered.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 API指示データCSVダウンロード",
                data=csv_api,
                file_name=f"api_instructions_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ APIデータ取得エラー: {e}")

    # 新規マッピング追加
    st.markdown("---")
    st.subheader("📝 新規マッピング追加")

    # 入力フォーム
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        lot_number = st.text_input("ロット番号", placeholder="例: F000000017")

    with col2:
        seino = st.text_input("SEINO（組立番号）", placeholder="例: K001")

    with col3:
        st.write("")  # スペース
        st.write("")  # スペース
        add_button = st.button("➕ 追加", use_container_width=True)

    if add_button:
        if lot_number and seino:
            try:
                engine = db_manager._connect_sqlite()
                with engine.connect() as conn:
                    insert_sql = text("""
                    INSERT OR REPLACE INTO manual_mappings
                    (lot_number, seino, updated_at)
                    VALUES (:lot_number, :seino, CURRENT_TIMESTAMP)
                    """)

                    conn.execute(insert_sql, {
                        'lot_number': lot_number.strip(),
                        'seino': seino.strip()
                    })
                    conn.commit()

                st.success(f"✅ マッピングを追加しました: {lot_number} → {seino}")
                st.rerun()

            except Exception as e:
                st.error(f"❌ エラー: {e}")
        else:
            st.warning("⚠️ ロット番号とSEINOを入力してください")

    # 既存のマッピング一覧
    st.markdown("---")
    st.subheader("📋 登録済みマッピング一覧")

    try:
        engine = db_manager._connect_sqlite()
        query = text("""
        SELECT
            id,
            lot_number AS ロット番号,
            seino AS SEINO,
            created_at AS 登録日時,
            updated_at AS 更新日時
        FROM manual_mappings
        ORDER BY updated_at DESC
        """)

        df = pd.read_sql(query, engine)

        if df.empty:
            st.info("ℹ️ 登録されているマッピングはありません")
        else:
            st.write(f"**総件数:** {len(df)}件")

            # データフレーム表示
            st.dataframe(
                df.drop('id', axis=1),
                use_container_width=True,
                height=400,
                hide_index=True
            )

            # 削除機能
            st.markdown("---")
            st.subheader("🗑️ マッピング削除")

            delete_col1, delete_col2 = st.columns([3, 1])

            with delete_col1:
                # 削除対象選択
                delete_options = df.apply(
                    lambda row: f"{row['ロット番号']} → {row['SEINO']}", axis=1
                ).tolist()

                selected_mapping = st.selectbox(
                    "削除するマッピングを選択",
                    options=delete_options,
                    index=None
                )

            with delete_col2:
                st.write("")  # スペース
                st.write("")  # スペース
                delete_button = st.button("🗑️ 削除", use_container_width=True, type="primary")

            if delete_button and selected_mapping:
                try:
                    selected_index = delete_options.index(selected_mapping)
                    selected_id = df.iloc[selected_index]['id']

                    with engine.connect() as conn:
                        delete_sql = text("DELETE FROM manual_mappings WHERE id = :id")
                        conn.execute(delete_sql, {'id': selected_id})
                        conn.commit()

                    st.success(f"✅ マッピングを削除しました: {selected_mapping}")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ エラー: {e}")

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")

    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
