"""
データベース接続テストスクリプト

EJデータベース（Oracle）とKRDデータベース（MySQL）への接続をテストします。
"""
import cx_Oracle
import pymysql
from sqlalchemy import create_engine

def test_ej_connection():
    """EJデータベース接続テスト"""
    print("\n=== EJデータベース（Oracle）接続テスト ===")
    try:
        connection_string = "EXPJ2/EXPJ2@172.17.107.102:1521/EXPJ"
        connection = cx_Oracle.connect(connection_string)
        cursor = connection.cursor()

        # M_ITEMテーブルの件数を取得
        cursor.execute("SELECT COUNT(*) FROM EXPJ2.M_ITEM")
        count = cursor.fetchone()[0]

        # サンプルデータを取得
        cursor.execute("SELECT ITEM_CD, PUCH_FIXED_LT FROM EXPJ2.M_ITEM WHERE ROWNUM <= 5")
        samples = cursor.fetchall()

        connection.close()

        print(f"✓ EJ接続成功")
        print(f"  M_ITEM総件数: {count:,}件")
        print(f"  サンプルデータ:")
        for item_cd, puch_fixed_lt in samples:
            print(f"    - {item_cd}: PUCH_FIXED_LT={puch_fixed_lt}")

        return True
    except Exception as e:
        print(f"✗ EJ接続失敗: {e}")
        return False

def test_krd_connection():
    """KRDデータベース接続テスト"""
    print("\n=== KRDデータベース（MySQL）接続テスト ===")
    try:
        connection = pymysql.connect(
            host='krd',
            user='pfw',
            password='mejiriHoo',
            database='machin',
            charset='utf8mb4'
        )
        cursor = connection.cursor()

        # DATA_RES_CAPAテーブルの件数を取得
        cursor.execute("SELECT COUNT(*) FROM DATA_RES_CAPA")
        count = cursor.fetchone()[0]

        # サンプルデータを取得
        cursor.execute("SELECT 品番, 工程, 設備 FROM DATA_RES_CAPA LIMIT 5")
        samples = cursor.fetchall()

        connection.close()

        print(f"✓ KRD接続成功")
        print(f"  DATA_RES_CAPA総件数: {count:,}件")
        print(f"  サンプルデータ:")
        for hinban, kotei, setsubi in samples:
            print(f"    - 品番:{hinban}, 工程:{kotei}, 設備:{setsubi}")

        return True
    except Exception as e:
        print(f"✗ KRD接続失敗: {e}")
        return False

def test_ej_query_example():
    """EJデータベースクエリ例"""
    print("\n=== EJデータベースクエリ例 ===")
    try:
        import pandas as pd

        connection_string = "EXPJ2/EXPJ2@172.17.107.102:1521/EXPJ"
        connection = cx_Oracle.connect(connection_string)

        sql = """
        SELECT ITEM_CD, PUCH_FIXED_LT, PRODUCT_TYP
        FROM EXPJ2.M_ITEM
        WHERE PRODUCT_TYP IN (6, 7, 8)
        AND ROWNUM <= 10
        """

        df = pd.read_sql(sql, connection)
        connection.close()

        print(f"✓ クエリ成功: {len(df)}件取得")
        print(df.to_string(index=False))

        return True
    except Exception as e:
        print(f"✗ クエリ失敗: {e}")
        return False

def test_krd_query_example():
    """KRDデータベースクエリ例"""
    print("\n=== KRDデータベースクエリ例 ===")
    try:
        import pandas as pd
        from sqlalchemy import create_engine

        connection_string = "mysql+pymysql://pfw:mejiriHoo@krd/machin"
        engine = create_engine(connection_string)

        sql = """
        SELECT 品番, 工程, 段取時間, 加工時間
        FROM DATA_RES_CAPA
        WHERE 品番 LIKE '5156-%'
        LIMIT 10
        """

        df = pd.read_sql(sql, engine)
        engine.dispose()

        print(f"✓ クエリ成功: {len(df)}件取得")
        print(df.to_string(index=False))

        return True
    except Exception as e:
        print(f"✗ クエリ失敗: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("データベース接続テスト")
    print("=" * 60)

    # 基本接続テスト
    ej_ok = test_ej_connection()
    krd_ok = test_krd_connection()

    # クエリ例テスト
    if ej_ok:
        test_ej_query_example()

    if krd_ok:
        test_krd_query_example()

    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"EJ接続: {'✓ 成功' if ej_ok else '✗ 失敗'}")
    print(f"KRD接続: {'✓ 成功' if krd_ok else '✗ 失敗'}")
    print("=" * 60)
