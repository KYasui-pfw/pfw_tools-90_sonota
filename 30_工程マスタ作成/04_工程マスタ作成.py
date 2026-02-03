# -*- coding: utf-8 -*-
"""
04_工程マスタ作成.py

03_5_カム課データ_前工程付き.csvから工程マスタを作成

処理内容:
  - 推定素材が"不明"でないデータを処理対象
  - 完成部番、工程１、子部番１、工程２、仕入先CD、単価、子部番２、備考、備考２（参考発注）の9列を出力
  - 個別処理1（MUL/ﾆｰﾄﾞﾙ/ALL）により工程２/仕入先CD/備考を設定
  - 子部番１による工程２変更（-MY/-MZ/-M1）
  - 個別処理2（EJ発注残参照、SKD11数字パターン）

出力:
  - work/04_工程マスタ.csv
"""

import sys
import csv
import re
import oracledb
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# 入力ファイル
INPUT_CSV = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work\03_5_カム課データ_前工程付き.csv")

# 出力先
OUTPUT_DIR = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work")
OUTPUT_CSV = OUTPUT_DIR / "04_マスター原本.csv"
OUTPUT_CSV_UNMATCH = OUTPUT_DIR / "04_個別処理未該当.csv"

# EJシステム接続情報
EJ_HOST = "172.17.107.102"
EJ_PORT = 1521
EJ_SERVICE = "EXPJ"
EJ_USER = "EXPJ2"
EJ_PASSWORD = "EXPJ2"

# oracledb thick mode初期化フラグ
_thick_mode_initialized = False


def init_oracle_thick_mode():
    """Oracle thick modeを初期化"""
    global _thick_mode_initialized
    if not _thick_mode_initialized:
        try:
            oracledb.init_oracle_client()
            _thick_mode_initialized = True
            print("  oracledb thick mode初期化完了")
        except Exception as e:
            print(f"  thick mode初期化スキップ: {e}")


def get_ej_connection():
    """EJシステムへの接続を取得"""
    init_oracle_thick_mode()
    dsn = oracledb.makedsn(EJ_HOST, EJ_PORT, service_name=EJ_SERVICE)
    return oracledb.connect(user=EJ_USER, password=EJ_PASSWORD, dsn=dsn)


def fetch_ej_order_data(item_codes):
    """
    EJ発注残テーブルから VEND_CD, PUCH_ODR_CD, UNIT_COST を取得

    Args:
        item_codes: 検索対象のITEM_CDリスト

    Returns:
        dict: {ITEM_CD: (VEND_CD, PUCH_ODR_CD, UNIT_COST)}（CREATED_DATE最新）
    """
    if not item_codes:
        return {}

    print(f"\nEJ発注残テーブルから取得中... (対象: {len(item_codes)}件)")

    # 重複除去
    unique_codes = list(set([code for code in item_codes if code]))
    if not unique_codes:
        return {}

    result = {}
    conn = get_ej_connection()
    try:
        cursor = conn.cursor()

        # バッチサイズ（IN句の制限対策）
        batch_size = 900

        for i in range(0, len(unique_codes), batch_size):
            batch = unique_codes[i:i + batch_size]
            placeholders = ','.join([f':p{j}' for j in range(len(batch))])

            # CREATED_DATE最新の行を取得
            sql = f"""
                SELECT
                    ITEM_CD,
                    VEND_CD,
                    PUCH_ODR_CD,
                    UNIT_COST,
                    CREATED_DATE
                FROM (
                    SELECT
                        ITEM_CD,
                        VEND_CD,
                        PUCH_ODR_CD,
                        UNIT_COST,
                        CREATED_DATE,
                        ROW_NUMBER() OVER (PARTITION BY ITEM_CD ORDER BY CREATED_DATE DESC) AS rn
                    FROM EXPJ2.T_RLSD_PUCH_ODR
                    WHERE ITEM_CD IN ({placeholders})
                )
                WHERE rn = 1
            """

            params = {f'p{j}': code for j, code in enumerate(batch)}
            cursor.execute(sql, params)

            for row in cursor:
                item_cd = row[0]
                vend_cd = row[1]
                puch_odr_cd = row[2]
                unit_cost = row[3]
                result[item_cd] = (vend_cd, puch_odr_cd, unit_cost)

            print(f"  バッチ {i // batch_size + 1}: {len(batch)}件処理完了")

        print(f"EJ発注残データ取得完了: {len(result)}品目")

    finally:
        conn.close()

    return result


def remove_parenthesis(text):
    """
    括弧以降を削除

    Args:
        text: 入力文字列

    Returns:
        str: 括弧以降を削除した文字列
    """
    if not text:
        return text

    # (または（の位置を探す
    pos1 = text.find('(')
    pos2 = text.find('（')

    # 両方見つからない場合
    if pos1 == -1 and pos2 == -1:
        return text

    # 両方見つかった場合は先に出現する方
    if pos1 != -1 and pos2 != -1:
        pos = min(pos1, pos2)
    elif pos1 != -1:
        pos = pos1
    else:
        pos = pos2

    return text[:pos]


def apply_common_logic(row):
    """
    共通処理を適用

    Returns:
        dict: 出力行データ
    """
    output = {
        '完成部番': row.get('加工部番', '').strip(),
        '工程１': 'CAFIN',
        '子部番１': '',
        '工程２': '',
        '仕入先CD': '',
        '単価': '',
        '単位数分子': '',
        '単位数分母': '',
        '子部番２': '',
        '備考': '',
        '備考２（参考発注）': ''
    }

    # 推定素材とカム課_子部番の取得
    estimated = row.get('推定素材', '').strip()
    kobuban = row.get('カム課_子部番', '').strip()

    # 子部番１のロジック
    if estimated == kobuban:
        # 同じ場合: 子部番１は空欄、子部番２に推定素材
        output['子部番１'] = ''
        output['子部番２'] = estimated
    else:
        # 異なる場合
        if 'Φ' in kobuban:
            # カム課_子部番にΦが含まれる場合: 子部番１は空欄
            output['子部番１'] = ''
        else:
            # 含まれない場合: 子部番１にカム課_子部番（括弧除去）
            output['子部番１'] = remove_parenthesis(kobuban)
        output['子部番２'] = estimated

    # === その他の処理（子部番１のクリーニング） ===
    kobuban1 = output['子部番１']

    # 【過去に同様の部番無し】が含まれる場合は空欄
    if '【過去に同様の部番無し】' in kobuban1:
        output['子部番１'] = ''
        kobuban1 = ''

    if kobuban1:  # 空欄でない場合のみ以下の処理を実行
        # 【】とその中身を削除
        kobuban1 = re.sub(r'【[^】]*】', '', kobuban1)

        # "-内作依頼"を削除
        kobuban1 = kobuban1.replace('-内作依頼', '')

        # "CUT数字"パターンを削除
        kobuban1 = re.sub(r'CUT\d+', '', kobuban1)

        # 全角スペース以降を削除
        pos = kobuban1.find('　')  # 全角スペース
        if pos != -1:
            kobuban1 = kobuban1[:pos]

        # 先頭・末尾の空白を削除
        kobuban1 = kobuban1.strip()

        # SKD11-DIAで始まる場合は空欄にする
        if kobuban1.startswith('SKD11-DIA'):
            kobuban1 = ''

        output['子部番１'] = kobuban1

    # === 単位数分子・単位数分母の取得 ===
    # 推定素材と一致する前工程Xを探し、対応する単位数分子X・単位数分母Xを取得
    estimated = row.get('推定素材', '').strip()
    for i in range(1, 7):  # 前工程1～6
        zenkohtei_col = f'前工程{i}'
        zenkohtei_value = row.get(zenkohtei_col, '').strip()

        if zenkohtei_value == estimated:
            # 一致した場合、対応する単位数分子・単位数分母を取得
            bunshi_col = f'単位数分子{i}'
            bunbo_col = f'単位数分母{i}'

            output['単位数分子'] = row.get(bunshi_col, '').strip()
            output['単位数分母'] = row.get(bunbo_col, '').strip()
            break

    # SKD11-DIA数字XL1000パターンの場合の特別処理
    # ※SKD長材と単純に金額で比較すれば、一つから100個取れるが、加工費を載せるので一つから50個取れると計算する。
    if not output['単位数分子'] and not output['単位数分母']:
        # 推定素材がSKD11-DIA数字XL1000パターンかチェック
        if re.match(r'^SKD11-DIA\d+XL1000$', estimated):
            output['単位数分子'] = '20'
            output['単位数分母'] = '1000'

    # それでも空欄の場合は、両方とも1をセット
    if not output['単位数分子'] and not output['単位数分母']:
        output['単位数分子'] = '1'
        output['単位数分母'] = '1'

    return output


def apply_individual_logic1(row, output):
    """
    個別処理1を適用（優先順位順）

    優先順位:
      1. カム課_工程に"MUL"が含まれる
      2. カム課_工程に"ﾆｰﾄﾞﾙ"が含まれる
      3. カム課_子部番に"ALL"が含まれる

    Returns:
        str: 適用された条件名（'MUL', 'ﾆｰﾄﾞﾙ', 'ALL', 'なし'）
    """
    kotei = row.get('カム課_工程', '').strip()
    kobuban = row.get('カム課_子部番', '').strip()

    # 優先度1: MUL
    if 'MUL' in kotei:
        output['工程２'] = 'SW'
        output['仕入先CD'] = '3200'
        output['備考'] = 'マルタス'
        return 'MUL'

    # 優先度2: ﾆｰﾄﾞﾙ
    if 'ﾆｰﾄﾞﾙ' in kotei:
        output['工程２'] = 'NC'
        output['仕入先CD'] = '3072'
        output['備考'] = 'ﾆｰﾄﾞﾙ'
        return 'ﾆｰﾄﾞﾙ'

    # 優先度3: ALL
    if 'ALL' in kobuban:
        output['工程２'] = 'NC'
        output['仕入先CD'] = '2829'
        output['備考'] = '寺内'
        return 'ALL'

    # いずれにも該当しない
    return 'なし'


def apply_kobuban_kotei_rule(output):
    """
    子部番１による工程２変更

    条件:
      - 子部番１に"-MY"または"-MZ"が含まれる
      - 子部番１の最後の3文字が"-M1"

    変更:
      - 工程２ = "M"
    """
    kobuban1 = output.get('子部番１', '').strip()
    if not kobuban1:
        return

    # -MY/-MZ含む、または末尾が-M1
    if '-MY' in kobuban1 or '-MZ' in kobuban1 or kobuban1.endswith('-M1'):
        output['工程２'] = 'M'


def apply_furisu_rule(row, output):
    """
    カム課_工程に"ﾌﾗｲｽ"が含まれる場合の処理

    変更:
      - 工程２ = "M"
      - 備考 = カム課_工程
    """
    kotei = row.get('カム課_工程', '').strip()
    if 'ﾌﾗｲｽ' in kotei:
        output['工程２'] = 'M'
        output['備考'] = kotei


def apply_individual_logic3(row, output):
    """
    個別処理3を適用（データ整形）

    処理:
      - 備考による仕入先CD設定
      - カム課_子部番に"NC"含む → 仕入先CD="2829", 工程２="NC"
      - 子部番２がSKD11数字で仕入先CD空欄 → 仕入先CD="1907", 工程２="SW"
    """
    biko = output.get('備考', '').strip()
    kobuban = row.get('カム課_子部番', '').strip()
    kobuban2 = output.get('子部番２', '').strip()
    shiirecd = output.get('仕入先CD', '').strip()

    # 備考による仕入先CD設定
    if biko == '寺内':
        output['仕入先CD'] = '2829'
    elif biko == 'ﾆｰﾄﾞﾙ':
        output['仕入先CD'] = '3072'
    elif biko == 'マルタス':
        output['仕入先CD'] = '3200'

    # カム課_子部番に"NC"含む
    if 'NC' in kobuban:
        output['仕入先CD'] = '2829'
        output['工程２'] = 'NC'

    # 子部番２がSKD11数字で仕入先CD空欄（フォールバック）
    if re.match(r'^SKD11\d+$', kobuban2) and not shiirecd:
        output['仕入先CD'] = '1907'
        output['工程２'] = 'SW'


def apply_individual_logic2(output, ej_data):
    """
    個別処理2を適用（EJ発注残参照）

    条件:
      - 推定素材が"SKD11数字"パターン → 工程２=SW
      - 推定素材が"SKD11-DIA"で始まる → 工程２=SW
      - 推定素材が"MA-"で始まる → 工程２=空欄、備考=空欄

    処理:
      - EJ発注残テーブルから VEND_CD, PUCH_ODR_CD, UNIT_COST を取得
      - 仕入先CD = VEND_CD
      - 備考２（参考発注） = PUCH_ODR_CD
      - 単価 = UNIT_COST

    Returns:
        bool: 適用されたかどうか
    """
    estimated = output.get('子部番２', '').strip()

    # パターン判定
    is_skd11_number = re.match(r'^SKD11\d+$', estimated)
    is_skd11_dia = estimated.startswith('SKD11-DIA')
    is_ma = estimated.startswith('MA-')

    # いずれのパターンにも該当しない場合は終了
    if not (is_skd11_number or is_skd11_dia or is_ma):
        return False

    # EJデータ取得
    if estimated not in ej_data:
        return False

    vend_cd, puch_odr_cd, unit_cost = ej_data[estimated]

    # 共通設定
    output['仕入先CD'] = vend_cd
    output['備考２（参考発注）'] = puch_odr_cd
    output['単価'] = str(unit_cost) if unit_cost is not None else ''

    # パターン別設定
    if is_skd11_number or is_skd11_dia:
        # SKD11数字またはSKD11-DIA → 工程２=SW
        output['工程２'] = 'SW'
    elif is_ma:
        # MA- → 工程２=空欄、備考=空欄
        output['工程２'] = ''
        output['備考'] = ''

    return True


def main():
    print("=" * 60)
    print("04_工程マスタ作成")
    print(f"入力: {INPUT_CSV}")
    print(f"出力: {OUTPUT_CSV}")
    print("=" * 60)

    # 入力ファイル確認
    if not INPUT_CSV.exists():
        print(f"エラー: 入力ファイルが見つかりません: {INPUT_CSV}")
        return False

    # 出力ディレクトリ確認
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # データ読み込み
    print("\nデータを読み込み中...")
    with open(INPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"総行数: {len(rows):,}行")

    # 処理対象の分類
    target_rows = [r for r in rows if r.get('推定素材', '').strip() != '不明']
    excluded_rows = [r for r in rows if r.get('推定素材', '').strip() == '不明']

    print(f"  処理対象（推定素材≠不明）: {len(target_rows):,}行")
    print(f"  処理対象外（推定素材=不明）: {len(excluded_rows):,}行")

    # EJ参照対象の推定素材を収集
    ej_target_materials = set()
    for row in target_rows:
        estimated = row.get('推定素材', '').strip()
        # SKD11数字パターン
        if re.match(r'^SKD11\d+$', estimated):
            ej_target_materials.add(estimated)
        # SKD11-DIAで始まる
        elif estimated.startswith('SKD11-DIA'):
            ej_target_materials.add(estimated)
        # MA-で始まる
        elif estimated.startswith('MA-'):
            ej_target_materials.add(estimated)

    print(f"\nEJ参照対象の推定素材: {len(ej_target_materials)}種類")

    # EJ発注残データ取得
    ej_data = {}
    if ej_target_materials:
        ej_data = fetch_ej_order_data(list(ej_target_materials))

    # 処理
    print("\n処理中...")
    output_rows = []
    output_rows_with_source = []  # (output_row, source_row)のペア
    logic1_stats = defaultdict(int)
    logic2_count = 0
    kotei_rule_count = 0
    furisu_rule_count = 0
    logic3_count = 0

    for row in target_rows:
        # 共通処理
        output_row = apply_common_logic(row)

        # 個別処理1
        condition = apply_individual_logic1(row, output_row)
        logic1_stats[condition] += 1

        # 個別処理2（全データ対象）
        if apply_individual_logic2(output_row, ej_data):
            logic2_count += 1

        # 子部番１による工程２変更
        before_kotei = output_row['工程２']
        apply_kobuban_kotei_rule(output_row)
        if output_row['工程２'] != before_kotei:
            kotei_rule_count += 1

        # ﾌﾗｲｽルール
        before_kotei2 = output_row['工程２']
        apply_furisu_rule(row, output_row)
        if output_row['工程２'] != before_kotei2:
            furisu_rule_count += 1

        # 個別処理3（データ整形）
        before_shiirecd = output_row['仕入先CD']
        apply_individual_logic3(row, output_row)
        if output_row['仕入先CD'] != before_shiirecd or output_row.get('工程２', ''):
            logic3_count += 1

        output_rows.append(output_row)
        output_rows_with_source.append((output_row, row))

    # 統計情報
    print(f"\n処理結果:")
    print(f"  出力行数: {len(output_rows):,}行")
    print(f"\n個別処理1:")
    print(f"  MUL: {logic1_stats['MUL']:,}件")
    print(f"  ﾆｰﾄﾞﾙ: {logic1_stats['ﾆｰﾄﾞﾙ']:,}件")
    print(f"  ALL: {logic1_stats['ALL']:,}件")
    print(f"  なし: {logic1_stats['なし']:,}件")
    print(f"\n個別処理2（EJ発注残参照）: {logic2_count:,}件")
    print(f"子部番１による工程２変更: {kotei_rule_count:,}件")
    print(f"ﾌﾗｲｽルール適用: {furisu_rule_count:,}件")
    print(f"個別処理3（データ整形）: {logic3_count:,}件")

    # 工程マスタ出力
    print(f"\n工程マスタを出力中: {OUTPUT_CSV}")
    output_fieldnames = ['完成部番', '工程１', '子部番１', '工程２', '仕入先CD', '単価', '単位数分子', '単位数分母', '子部番２', '備考', '備考２（参考発注）']
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    # 個別処理未該当ファイル出力（工程２が空欄の行）
    unmatch_rows = [source_row for output_row, source_row in output_rows_with_source
                    if not output_row['工程２'].strip()]

    if unmatch_rows:
        print(f"\n個別処理未該当を出力中: {OUTPUT_CSV_UNMATCH}")
        # 元の入力ファイルのフィールド名を使用
        input_fieldnames = list(target_rows[0].keys()) if target_rows else []
        with open(OUTPUT_CSV_UNMATCH, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=input_fieldnames)
            writer.writeheader()
            writer.writerows(unmatch_rows)
        print(f"  個別処理未該当: {len(unmatch_rows):,}行 → {OUTPUT_CSV_UNMATCH.name}")

    print(f"\n処理完了")
    print(f"  工程マスタ: {len(output_rows):,}行 → {OUTPUT_CSV.name}")
    if unmatch_rows:
        print(f"  個別処理未該当: {len(unmatch_rows):,}行 → {OUTPUT_CSV_UNMATCH.name}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
