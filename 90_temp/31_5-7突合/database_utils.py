"""
データベース接続ユーティリティ

EJデータベース（Oracle）とKRDデータベース（MySQL）への接続関数を提供します。
新しいスクリプトを作成する際は、このファイルから関数をインポートして使用してください。

使用例:
    from database_utils import ej_data_get, krd_data_get

    # EJからデータ取得
    ej_df = ej_data_get("SELECT * FROM EXPJ2.M_ITEM WHERE ROWNUM <= 10")

    # KRDからデータ取得
    krd_df = krd_data_get("SELECT * FROM DATA_RES_CAPA LIMIT 10")
"""

# NLS_LANG環境変数を設定（cx_Oracleをimportする前に設定する必要がある）
import os
os.environ['NLS_LANG'] = 'JAPANESE_JAPAN.AL32UTF8'

import cx_Oracle
import pandas as pd
from sqlalchemy import create_engine


def ej_data_get(sql):
    """
    EJシステム（Oracle Database）に接続してSQLを実行する

    Args:
        sql (str): 実行するSQL文

    Returns:
        pd.DataFrame: クエリ結果のDataFrame

    Raises:
        Exception: データベース接続またはクエリ実行時のエラー

    Example:
        >>> sql = "SELECT ITEM_CD, PUCH_FIXED_LT FROM EXPJ2.M_ITEM WHERE ROWNUM <= 5"
        >>> df = ej_data_get(sql)
        >>> print(df)
    """
    try:
        # EJシステム接続情報
        host = '172.17.107.102'
        port = '1521'
        service_name = 'EXPJ'
        username = 'EXPJ2'
        password = 'EXPJ2'

        # 接続文字列
        connection_string = f"{username}/{password}@{host}:{port}/{service_name}"

        # データベース接続
        connection = cx_Oracle.connect(connection_string)

        # SQLを実行してDataFrameに変換
        df = pd.read_sql(sql, connection)

        # 接続を閉じる
        connection.close()

        return df

    except Exception as e:
        print(f"EJシステムへの接続でエラーが発生しました: {str(e)}")
        raise


def krd_data_get(sql):
    """
    KRDシステム（MySQL Database）に接続してSQLを実行する

    Args:
        sql (str): 実行するSQL文

    Returns:
        pd.DataFrame: クエリ結果のDataFrame

    Raises:
        Exception: データベース接続またはクエリ実行時のエラー

    Example:
        >>> sql = "SELECT 品番, 工程, 設備 FROM DATA_RES_CAPA LIMIT 5"
        >>> df = krd_data_get(sql)
        >>> print(df)
    """
    try:
        # KRDシステム接続情報
        host = 'krd'
        user = 'pfw'
        password = 'mejiriHoo'
        database = 'machin'

        # 接続文字列（SQLAlchemy形式）
        connection_string = f"mysql+pymysql://{user}:{password}@{host}/{database}"

        # エンジン作成
        engine = create_engine(connection_string)

        # SQLを実行してDataFrameに変換
        df = pd.read_sql(sql, engine)

        # エンジンを閉じる
        engine.dispose()

        return df

    except Exception as e:
        print(f"KRDシステムへの接続でエラーが発生しました: {str(e)}")
        raise


def batch_query_ej(item_list, sql_template, batch_size=900):
    """
    EJデータベースに対して大量のITEM_CDを900件ずつバッチ処理でクエリする

    Oracle IN句の制限（1000件）を回避するためのバッチ処理関数。

    Args:
        item_list (list): ITEM_CDのリスト
        sql_template (str): SQLテンプレート（{item_list}プレースホルダーを含む）
        batch_size (int): バッチサイズ（デフォルト900、最大999）

    Returns:
        pd.DataFrame: 全バッチの結果を結合したDataFrame

    Example:
        >>> items = ['K-24913AB', 'K-24913AC', ...]  # 1500件のリスト
        >>> sql_template = '''
        ...     SELECT ITEM_CD, PUCH_FIXED_LT
        ...     FROM EXPJ2.M_ITEM
        ...     WHERE ITEM_CD IN ({item_list})
        ... '''
        >>> df = batch_query_ej(items, sql_template)
        >>> print(f"取得件数: {len(df)}")
    """
    all_results = []

    for i in range(0, len(item_list), batch_size):
        batch = item_list[i:i + batch_size]
        item_sql_list = "','".join(batch)

        # SQLテンプレートにITEM_CDリストを埋め込み
        sql = sql_template.replace('{item_list}', f"'{item_sql_list}'")

        batch_df = ej_data_get(sql)
        all_results.append(batch_df)
        print(f"バッチ{i//batch_size + 1}: {len(batch)}件 -> {len(batch_df)}行取得")

    # 全バッチを結合
    if all_results:
        result_df = pd.concat(all_results, ignore_index=True)
    else:
        result_df = pd.DataFrame()

    return result_df


def test_connections():
    """
    EJとKRDの両方のデータベース接続をテストする

    Returns:
        tuple: (ej_success, krd_success) - 各データベースの接続成功/失敗

    Example:
        >>> ej_ok, krd_ok = test_connections()
        >>> if ej_ok and krd_ok:
        ...     print("全データベース接続成功")
    """
    print("=== データベース接続テスト ===")

    # EJ接続テスト
    ej_success = False
    try:
        sql = "SELECT COUNT(*) as cnt FROM EXPJ2.M_ITEM WHERE ROWNUM <= 1"
        df = ej_data_get(sql)
        print(f"✓ EJ接続成功")
        ej_success = True
    except Exception as e:
        print(f"✗ EJ接続失敗: {e}")

    # KRD接続テスト
    krd_success = False
    try:
        sql = "SELECT COUNT(*) as cnt FROM DATA_RES_CAPA LIMIT 1"
        df = krd_data_get(sql)
        print(f"✓ KRD接続成功")
        krd_success = True
    except Exception as e:
        print(f"✗ KRD接続失敗: {e}")

    return ej_success, krd_success


if __name__ == "__main__":
    # このファイルを直接実行した場合は接続テストを実行
    print("=" * 60)
    print("データベース接続ユーティリティ - 接続テスト")
    print("=" * 60)

    ej_ok, krd_ok = test_connections()

    if ej_ok:
        print("\n=== EJサンプルクエリ ===")
        sql = """
        SELECT ITEM_CD, PUCH_FIXED_LT
        FROM EXPJ2.M_ITEM
        WHERE ROWNUM <= 5
        """
        df = ej_data_get(sql)
        print(df.to_string(index=False))

    if krd_ok:
        print("\n=== KRDサンプルクエリ ===")
        sql = """
        SELECT 品番, 工程, 設備
        FROM DATA_RES_CAPA
        LIMIT 5
        """
        df = krd_data_get(sql)
        print(df.to_string(index=False))

    print("\n" + "=" * 60)
    print(f"テスト結果: EJ={'成功' if ej_ok else '失敗'}, KRD={'成功' if krd_ok else '失敗'}")
    print("=" * 60)
