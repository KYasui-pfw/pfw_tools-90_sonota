"""
view_report_405 のカラム一覧を確認するスクリプト
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DB_URL = os.getenv('DB_URL', 'postgresql://postgres:cimtops@ESRV10/irepodb')

try:
    engine = create_engine(DB_URL, echo=False)

    with engine.connect() as connection:
        # カラム一覧を取得
        result = connection.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'view_report_405'
            AND column_name LIKE 'cluster%'
            ORDER BY column_name
        """))

        print("view_report_405 のcluster列:")
        print("=" * 60)
        for row in result:
            print(f"{row[0]:<30} {row[1]}")

        print("\n\nTop_remark3の確認:")
        result2 = connection.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'view_report_405'
            AND column_name LIKE '%remark%'
            ORDER BY column_name
        """))
        for row in result2:
            print(f"{row[0]:<30} {row[1]}")

except Exception as e:
    print(f"エラー: {e}")
