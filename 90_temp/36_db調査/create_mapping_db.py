"""
create_mapping_db.py

mapping_results.xlsx の「マッピングデータ」シートから
mapping.db を作成するスクリプト

入力: mapping_results.xlsx
出力: mapping.db
"""
import pandas as pd
import sqlite3
import os

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "mapping_results.xlsx")
OUTPUT_DB = os.path.join(SCRIPT_DIR, "mapping.db")
SHEET_NAME = "マッピングデータ"


def split_rbom(val):
    """rBOM発注番号+行番号を分割"""
    if pd.isna(val):
        return None, None
    parts = str(val).split('+')
    if len(parts) == 2:
        return parts[0], int(parts[1])
    return str(val), None


def main():
    print("=" * 50)
    print("mapping.db 作成処理")
    print("=" * 50)
    print()

    # 入力ファイル確認
    print(f"[DEBUG] SCRIPT_DIR: {SCRIPT_DIR}")
    print(f"[DEBUG] INPUT_FILE: {INPUT_FILE}")
    print(f"[DEBUG] OUTPUT_DB: {OUTPUT_DB}")

    if not os.path.exists(INPUT_FILE):
        print(f"エラー: 入力ファイルが見つかりません: {INPUT_FILE}")
        return 1

    print(f"入力ファイル: {INPUT_FILE}")
    print(f"出力先: {OUTPUT_DB}")
    print()

    # Excel読み込み
    print(f"シート「{SHEET_NAME}」を読み込み中...")
    try:
        df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)
    except Exception as e:
        print(f"[DEBUG] Excel読み込みエラー: {type(e).__name__}: {e}")
        raise

    cols = df.columns.tolist()
    print(f"[DEBUG] カラム数: {len(cols)}")
    print(f"[DEBUG] カラム一覧:")
    for i, col in enumerate(cols):
        print(f"  [{i}] {col}")

    print(f"読み込み行数: {len(df)}")
    print()

    # 必要なカラムを抽出
    # カラムインデックス: 2=状態, 4=EJ発注番号, 13=rBOM発注番号+行番号, 14=rBOM連番, 17=rBOM数
    print(f"[DEBUG] 使用するカラムインデックス: 2, 4, 13, 14, 17")
    print(f"[DEBUG] カラム[2] (状態): {cols[2] if len(cols) > 2 else 'インデックス範囲外'}")
    print(f"[DEBUG] カラム[4] (EJ発注番号): {cols[4] if len(cols) > 4 else 'インデックス範囲外'}")
    print(f"[DEBUG] カラム[13] (rBOM発注番号+行番号): {cols[13] if len(cols) > 13 else 'インデックス範囲外'}")
    print(f"[DEBUG] カラム[14] (rBOM連番): {cols[14] if len(cols) > 14 else 'インデックス範囲外'}")
    print(f"[DEBUG] カラム[17] (rBOM数): {cols[17] if len(cols) > 17 else 'インデックス範囲外'}")

    if len(cols) <= 17:
        print(f"[DEBUG] エラー: カラム数が不足しています。最低18カラム必要ですが、{len(cols)}カラムしかありません。")
        return 1

    try:
        ej_order_no = df[cols[4]]
        rbom_combined = df[cols[13]]
        rbom_quantity = df[cols[17]]
        rbom_m_sequence = df[cols[14]]
        status = df[cols[2]]
    except Exception as e:
        print(f"[DEBUG] カラム抽出エラー: {type(e).__name__}: {e}")
        raise

    print(f"[DEBUG] 各カラムのサンプル値（先頭5行）:")
    print(f"  EJ発注番号: {ej_order_no.head().tolist()}")
    print(f"  rBOM発注番号+行番号: {rbom_combined.head().tolist()}")
    print(f"  rBOM数: {rbom_quantity.head().tolist()}")
    print(f"  rBOM連番: {rbom_m_sequence.head().tolist()}")
    print(f"  状態: {status.head().tolist()}")

    # rBOM発注番号+行番号を分割
    print("[DEBUG] rBOM発注番号+行番号を分割中...")
    rbom_order_no = []
    rbom_line_no = []
    for i, val in enumerate(rbom_combined):
        try:
            order, line = split_rbom(val)
            rbom_order_no.append(order)
            rbom_line_no.append(line)
        except Exception as e:
            print(f"[DEBUG] 行{i}で分割エラー: val={val}, エラー={type(e).__name__}: {e}")
            raise

    print(f"[DEBUG] 分割完了: {len(rbom_order_no)}件")

    # DataFrame作成
    print("[DEBUG] DataFrame作成中...")
    try:
        new_df = pd.DataFrame({
            'ej_order_no': ej_order_no,
            'rbom_order_no': rbom_order_no,
            'rbom_line_no': rbom_line_no,
            'rbom_quantity': rbom_quantity,
            'rbom_m_sequence': rbom_m_sequence,
            'status': status
        })
        print(f"[DEBUG] DataFrame作成完了: {len(new_df)}行")
        print(f"[DEBUG] DataFrame dtypes:\n{new_df.dtypes}")
    except Exception as e:
        print(f"[DEBUG] DataFrame作成エラー: {type(e).__name__}: {e}")
        raise

    # 既存DBがあれば削除
    if os.path.exists(OUTPUT_DB):
        os.remove(OUTPUT_DB)
        print(f"既存のDBを削除しました: {OUTPUT_DB}")

    # SQLiteデータベース作成
    print("データベース作成中...")
    try:
        conn = sqlite3.connect(OUTPUT_DB)
        print(f"[DEBUG] SQLite接続成功: {OUTPUT_DB}")
    except Exception as e:
        print(f"[DEBUG] SQLite接続エラー: {type(e).__name__}: {e}")
        raise

    # 一時テーブルにデータ挿入
    print("[DEBUG] 一時テーブルにデータ挿入中...")
    try:
        new_df.to_sql('mapping_results_temp', conn, if_exists='replace', index=False)
        print("[DEBUG] 一時テーブル作成完了")
    except Exception as e:
        print(f"[DEBUG] 一時テーブル作成エラー: {type(e).__name__}: {e}")
        raise

    # 正しい型でテーブル作成
    print("[DEBUG] mapping_resultsテーブル作成中...")
    try:
        conn.execute('''
            CREATE TABLE mapping_results (
                ej_order_no TEXT,
                rbom_order_no TEXT,
                rbom_line_no INTEGER,
                rbom_quantity REAL,
                rbom_m_sequence INTEGER,
                status TEXT
            )
        ''')
        print("[DEBUG] mapping_resultsテーブル作成完了")
    except Exception as e:
        print(f"[DEBUG] テーブル作成エラー: {type(e).__name__}: {e}")
        raise

    # データを変換して挿入（INTEGER型に変換）
    print("[DEBUG] データ挿入中...")
    try:
        conn.execute('''
            INSERT INTO mapping_results (ej_order_no, rbom_order_no, rbom_line_no, rbom_quantity, rbom_m_sequence, status)
            SELECT
                ej_order_no,
                rbom_order_no,
                CAST(rbom_line_no AS INTEGER),
                rbom_quantity,
                CAST(rbom_m_sequence AS INTEGER),
                status
            FROM mapping_results_temp
        ''')
        print("[DEBUG] データ挿入完了")
    except Exception as e:
        print(f"[DEBUG] データ挿入エラー: {type(e).__name__}: {e}")
        raise

    # 一時テーブル削除
    print("[DEBUG] 一時テーブル削除中...")
    conn.execute('DROP TABLE mapping_results_temp')

    # インデックス作成
    print("[DEBUG] インデックス作成中...")
    conn.execute('CREATE INDEX idx_ej_order_no ON mapping_results(ej_order_no)')
    conn.execute('CREATE INDEX idx_status ON mapping_results(status)')
    print("[DEBUG] インデックス作成完了")

    conn.commit()
    print("[DEBUG] コミット完了")

    # 確認
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM mapping_results')
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mapping_results WHERE status IN ('済', '済2', '手')")
    target = cursor.fetchone()[0]

    conn.close()

    # 結果表示
    print()
    print("=" * 50)
    print("作成完了")
    print("=" * 50)
    print(f"総レコード数: {total}")
    print(f"SQLで取得対象（status IN '済','済2','手'）: {target}件")
    print(f"ファイルサイズ: {os.path.getsize(OUTPUT_DB):,} bytes")
    print()

    return 0


if __name__ == "__main__":
    exit(main())
