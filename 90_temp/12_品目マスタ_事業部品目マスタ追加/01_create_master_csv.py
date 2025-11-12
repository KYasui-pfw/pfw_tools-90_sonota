"""
品目マスタ・事業部別品目マスタのCSVデータ生成スクリプト

入力: 01_input フォルダ内のCSV（主キーのみ）
出力: 02_output フォルダ内のCSV（全カラム、固定値設定済み）
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# ========================================
# 固定値設定
# ========================================

# M0810 品目マスタの固定値
M0810_FIXED_VALUES = {
    # デフォルト値あり（テーブル定義より）
    'STDGNKKSKBN': '1',      # 基準原価係数適用
    'KKNAIBTNKKBN': '1',     # 国内売単価係数適用
    'KTTNKIKBN': '2',        # 工程展開用区分
    'SYUKOKBN': '1',         # 出庫区分
    'CVDOKONKBN': '2',       # コンバージョン時同梱区分
    'CLASSNM': ' ',          # クラス名

    # 空欄設定項目
    'HMWNM': '',             # 品名(全角) - 空欄
    'MODELW': '',            # 型式(全角) - 空欄

    # NOT NULL制約あり、デフォルトなし → 固定値設定が必要
    # ※これらの値は業務要件に応じて変更してください
    'HMNM': '',              # 品名
    'HMKBN': '',             # 品目区分
    'HMGUNCD': '',           # 品目群コード
    'HMBUNCD': '',           # 品目分類コード
    'ZUNITCD': '',           # 在庫単位コード
    'WEIGHT': 0.000,         # 品目重量
    'HUNITCD': '',           # 発注単位コード
    'HIRIQTY': 0.00,         # 入数
    'PKBN': '',              # 単価区分
    'RCVTSTKBN': '',         # 受入検査区分
    'RCVCHKKBN': '',         # 受入検収区分
    'SUPLT': 0,              # 調達リードタイム
    'TAXKBN': '',            # 標準消費税区分
    'COST': 0.00,            # 標準原単価
    'SHAPEKBN': '',          # 形状
    'SHAPEQTY': 0.000,       # 形状量
    'SHAPEUNIT': '',         # 形状単位コード
    'KTEXPKBN': '',          # 工程自動展開区分
    'ATEXPKBN': '',          # 自動展開区分
    'EXPSTPKBN': '',         # 展開停止区分
    'VALFLG': '',            # 有効状態
    'MISUMIHNKBN': '',       # ミスミ品区分
}

# M0820 事業部別品目マスタの固定値
M0820_FIXED_VALUES = {
    # デフォルト値あり（テーブル定義より）
    'NNKBN': '2',            # 納入区分

    # NOT NULL制約あり、デフォルトなし → 固定値設定が必要
    # ※これらの値は業務要件に応じて変更してください
    'ZIKNKBN': '',           # 在庫管理区分
    'VALZIKBN': '',          # 有効在庫マイナス許可区分
    'AZQTY': 0.00,           # 安全在庫数
    'EDPRICEKBN': '',        # 完成単価区分
    'MNHKKBN': '',           # 月次評価計算区分
    'ZIHKKBN': '',           # 在庫評価区分
    'HKPRICE': 0.00,         # 評価単価
    'YTPRICE': 0.00,         # 予定単価
    'EITHKBN': '',           # 営業手配区分
    'ZIREPQTY': 0.00,        # 在庫補充量
    'SUMMARYDAY': 0,         # 手配納期丸め日数
    'ZAIKOKBN': '',          # 在庫区分
    'HKRANKCD': '',          # 在庫評価ランクコード
    'ATDENKBN': '',          # 自動手配伝票区分
}

# ========================================
# M0810 全カラムリスト（定義順）
# ========================================
M0810_COLUMNS = [
    'HMCD', 'HMNM', 'HMWNM', 'MODEL', 'MODELW', 'MAKER', 'MATERIAL', 'PROCESS',
    'HMKBN', 'HMGUNCD', 'HMBUNCD', 'BUCD', 'CSBCD', 'ZUNITCD', 'WEIGHT',
    'HUNITCD', 'HIRIQTY', 'PKBN', 'RCVTSTKBN', 'RCVCHKKBN', 'SUPLT', 'TAXKBN',
    'COST', 'PRICE', 'SHAPEKBN', 'SIZEX', 'SIZEY', 'SIZEZ', 'SHAPEQTY',
    'SHAPEUNIT', 'KTEXPKBN', 'ATEXPKBN', 'EXPSTPKBN', 'SEIKBN', 'STOPDT',
    'STOPNOTE', 'NOTE', 'VALFLG',
    'MISUMIHNKBN', 'STDGNKKSKBN', 'KKNAIBTNKKBN', 'KTTNKIKBN', 'SYUKOKBN',
    'CVDOKONKBN', 'SECTION', 'CLASSNM', 'EGROUP', 'CAT', 'HEATTRTMT',
    'SURFTRTTMT', 'NTCD'
]

# ========================================
# M0820 全カラムリスト（定義順）
# ========================================
M0820_COLUMNS = [
    'HMCD', 'KNRBUCD', 'ZIKNKBN', 'VALZIKBN', 'SRCD', 'SRPRICE', 'SUPCLSCD',
    'SUPCD', 'TNBAN', 'AZQTY', 'EDPRICEKBN', 'MNHKKBN', 'ZIHKKBN', 'HKPRICE',
    'YTPRICE', 'BRANCHNO', 'EITHKBN',
    'ZIREPQTY', 'SUMMARYDAY', 'HKNKCD', 'ZAIKOKBN', 'HKRANKCD', 'HKRANKCDHIS',
    'STDT17', 'STPRICE17', 'ZAIKOKBN17', 'NNKBN', 'NNCD', 'NNBASHO', 'ATDENKBN'
]

# ========================================
# ディレクトリ設定
# ========================================
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / '01_input'
OUTPUT_DIR = BASE_DIR / '02_output'
WORK_DIR = BASE_DIR / '03_work'

# 入力ファイル（振り分け処理の結果）
INPUT_CSV = WORK_DIR / '01_存在しない.csv'

# ディレクトリ作成
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
WORK_DIR.mkdir(exist_ok=True)


def create_m0810_csv(input_csv: Path, output_csv: Path):
    """
    M0810 品目マスタのCSVデータを生成

    Args:
        input_csv: 入力CSVファイルパス（品目コードまたはHMCD列）
        output_csv: 出力CSVファイルパス（全カラム）
    """
    print(f"処理開始: {input_csv.name}")

    # 入力CSVを読み込み
    df_input = pd.read_csv(input_csv, dtype=str, encoding='utf-8-sig')

    # 品目コード列の確認（'品目コード' または 'HMCD'）
    if '品目コード' in df_input.columns:
        hmcd_column = '品目コード'
    elif 'HMCD' in df_input.columns:
        hmcd_column = 'HMCD'
    else:
        raise ValueError(f"入力CSVに'品目コード'または'HMCD'カラムが存在しません: {input_csv}")

    # 新しいDataFrameを作成（全カラム）
    df_output = pd.DataFrame(columns=M0810_COLUMNS)

    # 主キー（HMCD）をコピー
    df_output['HMCD'] = df_input[hmcd_column]

    # 固定値を設定
    for column, value in M0810_FIXED_VALUES.items():
        if column in df_output.columns:
            df_output[column] = value

    # CSVとして出力
    df_output.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"  → 出力完了: {output_csv.name} (レコード数: {len(df_output)})")


def create_m0820_csv(input_csv: Path, output_csv: Path):
    """
    M0820 事業部別品目マスタのCSVデータを生成

    Args:
        input_csv: 入力CSVファイルパス（HMCD, KNRBUCD列）
        output_csv: 出力CSVファイルパス（全カラム）
    """
    print(f"処理開始: {input_csv.name}")

    # 入力CSVを読み込み
    df_input = pd.read_csv(input_csv, dtype=str)

    # HMCD, KNRBUCDカラムが存在するか確認
    if 'HMCD' not in df_input.columns or 'KNRBUCD' not in df_input.columns:
        raise ValueError(f"入力CSVに'HMCD'と'KNRBUCD'カラムが必要です: {input_csv}")

    # 新しいDataFrameを作成（全カラム）
    df_output = pd.DataFrame(columns=M0820_COLUMNS)

    # 主キー（HMCD, KNRBUCD）をコピー
    df_output['HMCD'] = df_input['HMCD']
    df_output['KNRBUCD'] = df_input['KNRBUCD']

    # 固定値を設定
    for column, value in M0820_FIXED_VALUES.items():
        if column in df_output.columns:
            df_output[column] = value

    # CSVとして出力
    df_output.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"  → 出力完了: {output_csv.name} (レコード数: {len(df_output)})")


def main():
    """メイン処理"""
    print("=" * 60)
    print("品目マスタ・事業部別品目マスタ CSV生成処理")
    print("=" * 60)

    # 入力ファイルの存在確認
    if not INPUT_CSV.exists():
        print(f"エラー: 入力ファイルが見つかりません: {INPUT_CSV}")
        print("先に 00_split_by_existing.py を実行してください。")
        return

    # 出力ファイルパス
    m0810_output = OUTPUT_DIR / 'M0810_output.csv'
    m0820_output = OUTPUT_DIR / 'M0820_output.csv'

    # M0810の処理
    print()
    print("【M0810 品目マスタ生成】")
    create_m0810_csv(INPUT_CSV, m0810_output)

    print()
    print("【M0820 事業部別品目マスタ生成】")
    # M0820は主キーがHMCD + KNRBUCDのため、KNRBUCDが必要
    # ※KNRBUCDの値は業務要件に応じて設定してください
    print("  ※ M0820は主キー(HMCD + KNRBUCD)が必要です")
    print("  ※ 現在の入力CSVには品目コードのみ含まれています")
    print("  ※ KNRBUCDの設定が必要な場合は、入力CSVにKNRBUCD列を追加してください")
    # create_m0820_csv(INPUT_CSV, m0820_output)  # KNRBUCDが必要なため一旦コメントアウト

    print()
    print("=" * 60)
    print("処理完了")
    print("=" * 60)


if __name__ == '__main__':
    main()
