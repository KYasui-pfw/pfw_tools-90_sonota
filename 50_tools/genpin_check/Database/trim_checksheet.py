import sqlite3
import os
import sys

# --- 設定 ---
# スクリプト自身の絶対パスを取得し、そこを基準にDBファイルを探す
try:
    _script_path = os.path.abspath(__file__)
    _script_dir = os.path.dirname(_script_path)
    DB_FILE = os.path.join(_script_dir, 'checksheet.db')
except NameError:
    # 対話モードなどで__file__が定義されていない場合のフォールバック
    DB_FILE = 'checksheet.db'
    
# テーブル名
TABLE_NAME = 'zubancheck'
# ----------------

def convert_to_zenkaku(number_str):
    """半角数字の文字列を全角数字の文字列に変換します。"""
    zenkaku_map = str.maketrans('0123456789', '０１２３４５６７８９')
    return number_str.translate(zenkaku_map)

def cleanup_db_columns_with_conditions():
    """
    SQLiteデータベースの指定カラムに対し、条件付きのクリーンアップ処理を行います。
    """
    # データベースファイルが存在するか確認
    if not os.path.exists(DB_FILE):
        print(f"エラー: データベースファイル '{DB_FILE}' が見つかりません。")
        print("Pythonスクリプトと同じフォルダに 'checksheet.db' を置いてください。")
        # エラーで終了する場合、終了コードを返すのが一般的
        sys.exit(1)

    conn = None
    try:
        # データベースに接続
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        print(f"データベース '{DB_FILE}' に接続しました。")

        # 更新対象となるカラム名のリストを動的に生成
        columns_to_update = []
        for i in range(1, 16):
            zenkaku_num = convert_to_zenkaku(str(i))
            columns_to_update.append(f"チェック項目{zenkaku_num}")
            columns_to_update.append(f"チェック基準{zenkaku_num}")
        
        # 削除対象とする空白文字を定義
        whitespace_chars = "' 　' || CHAR(9) || CHAR(10) || CHAR(13)"

        # 各カラムに対してクリーンアップ処理を実行
        print("クリーンアップ処理を開始します...")
        successful_updates = 0
        for column in columns_to_update:
            # SQLiteのCASE式を使って条件分岐を実現
            sql_query = f'''
                UPDATE {TABLE_NAME}
                SET "{column}" = 
                    CASE
                        WHEN TRIM("{column}", {whitespace_chars}) IN ('-', '－') THEN
                            TRIM("{column}", {whitespace_chars})
                        ELSE
                            RTRIM(
                                REPLACE(REPLACE("{column}", CHAR(13), ''), CHAR(10), ''),
                                ' 　' || CHAR(9)
                            )
                    END
                WHERE "{column}" IS NOT NULL;
            '''
            
            try:
                cursor.execute(sql_query)
                if cursor.rowcount > 0:
                    print(f"  - カラム '{column}' を更新しました。({cursor.rowcount}行影響)")
                    successful_updates += cursor.rowcount
            except sqlite3.OperationalError:
                print(f"  - 警告: カラム '{column}' がテーブル '{TABLE_NAME}' に存在しない可能性があります。スキップします。")

        # 変更をデータベースに保存（コミット）
        conn.commit()

        print("\n処理が完了しました。")
        if successful_updates > 0:
            print(f"合計 {successful_updates} 件のデータ更新をデータベースに保存しました。")
        else:
            print("更新対象のデータは見つかりませんでした。")

    except sqlite3.Error as e:
        print(f"\nデータベースエラーが発生しました: {e}")
        if conn:
            conn.rollback()
            print("エラーが発生したため、変更はすべて元に戻されました。")
        sys.exit(1)

    finally:
        if conn:
            conn.close()
            print("データベース接続を閉じました。")

if __name__ == '__main__':
    cleanup_db_columns_with_conditions()
    # バッチファイルで実行した際にウィンドウがすぐ閉じないようにするため
    #input("何かキーを押すと終了します...")
