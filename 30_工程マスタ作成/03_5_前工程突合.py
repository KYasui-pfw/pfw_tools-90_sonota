# -*- coding: utf-8 -*-
"""
03_5_前工程突合.py

02_5_カム課データ_重複削除.csvと03_前工程横展開_有効データ.csvを汎用的に突合

突合条件:
  条件1グループ: 加工部番を使用
  条件2グループ: カム課_子部番を使用
  条件3グループ: カム課_孫部番を使用

各グループで、完成部番、前工程1〜5と突合し、マッチした後続の前工程を追加

出力:
  - work/03_5_カム課データ_前工程付き.csv
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

# 入力ファイル
INPUT_CAM = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work\02_5_カム課データ_重複削除.csv")
INPUT_ZENKOHTEI = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work\03_前工程横展開_有効データ.csv")
INPUT_NEEDLE = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work\ニードルデータ.csv")

# 出力先
OUTPUT_DIR = Path(r"C:\Dev\90_tools\30_工程マスタ作成\work")
OUTPUT_CSV = OUTPUT_DIR / "03_5_カム課データ_前工程付き.csv"


def is_not_empty(value):
    """値が空欄でないかチェック"""
    if value is None:
        return False
    s = str(value).strip()
    return s != '' and s != '0' and s.lower() != 'nan'


def load_zenkohtei_data(file_path):
    """
    前工程データを読み込み、各カラムごとにインデックスを作成

    Returns:
        dict: {カラム名: {値: [前工程データリスト]}}
    """
    print("\n前工程データを読み込み中...")

    # インデックス: カラム名 → 値 → データリスト
    indexes = {
        '完成部番': defaultdict(list),
        '前工程1': defaultdict(list),
        '前工程2': defaultdict(list),
        '前工程3': defaultdict(list),
        '前工程4': defaultdict(list),
        '前工程5': defaultdict(list)
    }

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)  # ヘッダースキップ

        for row in reader:
            if len(row) < 20:
                continue

            # 各カラムを取得
            data = {
                '完成部番': row[1].strip() if len(row) > 1 else '',
                '単位数分子1': row[2].strip() if len(row) > 2 else '',
                '単位数分母1': row[3].strip() if len(row) > 3 else '',
                '前工程1': row[4].strip() if len(row) > 4 else '',
                '単位数分子2': row[5].strip() if len(row) > 5 else '',
                '単位数分母2': row[6].strip() if len(row) > 6 else '',
                '前工程2': row[7].strip() if len(row) > 7 else '',
                '単位数分子3': row[8].strip() if len(row) > 8 else '',
                '単位数分母3': row[9].strip() if len(row) > 9 else '',
                '前工程3': row[10].strip() if len(row) > 10 else '',
                '単位数分子4': row[11].strip() if len(row) > 11 else '',
                '単位数分母4': row[12].strip() if len(row) > 12 else '',
                '前工程4': row[13].strip() if len(row) > 13 else '',
                '単位数分子5': row[14].strip() if len(row) > 14 else '',
                '単位数分母5': row[15].strip() if len(row) > 15 else '',
                '前工程5': row[16].strip() if len(row) > 16 else '',
                '単位数分子6': row[17].strip() if len(row) > 17 else '',
                '単位数分母6': row[18].strip() if len(row) > 18 else '',
                '前工程6': row[19].strip() if len(row) > 19 else ''
            }

            # 各カラムでインデックス化
            for col_name in ['完成部番', '前工程1', '前工程2', '前工程3', '前工程4', '前工程5']:
                value = data[col_name]
                if value:  # 空でない場合のみインデックスに追加
                    indexes[col_name][value].append(data)

    # 統計情報
    for col_name, index in indexes.items():
        print(f"  {col_name}: {len(index):,}件")

    return indexes


def load_needle_data(file_path):
    """
    ニードルデータを読み込み

    Returns:
        list: [(ニードル加工部番, 部品名補足, is_wildcard), ...]
    """
    if not file_path.exists():
        print(f"\n警告: ニードルデータが見つかりません: {file_path}")
        return []

    print("\nニードルデータを読み込み中...")

    needle_data = []
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)  # ヘッダースキップ

        for row in reader:
            if len(row) < 1:
                continue

            needle_buban = row[0].strip()
            buhinmei_hosoku = row[1].strip() if len(row) > 1 else ''

            if not needle_buban:
                continue

            # ワイルドカード判定
            is_wildcard = '*' in needle_buban

            needle_data.append((needle_buban, buhinmei_hosoku, is_wildcard))

    print(f"  ニードルデータ: {len(needle_data):,}件（ワイルドカード含む）")
    return needle_data


def apply_estimated_material(row):
    """
    推定素材を設定

    ロジック:
      1. 前工程1〜6で空欄でない一番右の項目 → その値をセット
      2. カム課_子部番に「Φ数字2桁」がある → SKD11-DIA{数字}XL1000
      3. カム課_子部番に「SKD11-DIA数字」がある → SKD11-DIA{数字}XL1000
      4. カム課_子部番が「MA」から始まる → そのまま推定素材にセット
      5. 個別対応マッピング（15パターン）
      6. 上記いずれも該当しない → 不明

    Args:
        row: カム課データの1行（dict）
    """
    import re

    # 個別対応マッピング
    individual_mappings = {
        'SKD7.0X40': 'SKD11040082',
        'SKD7.0X50': 'SKD11050085',
        'SKD9.0X50': 'SKD11030085',
        'SKD6.0X47': 'SKD11047067',
        'SKD6.0X35': 'SKD11035067',
        'SKD6.0X30': 'SKD11030070',
        'SKD5.95X27': 'SKD11027067',
        'SKD5.7X47': 'SKD11047067',
        'SKD4.8X30': 'SKD11030055',
        'SKD4.2X25': 'SKD11025055',
        'SKD25X19': 'SKD11021082',
        'SKD1616': 'SKD11030085',
        'SK5-3X22': 'SKD11030085',
        'SKD6G2540': 'SKD11025067',
        'SKD5Z1236': 'SKD11012050',
        'NC-5': 'SKD11025067'
    }

    # 前工程1〜6をチェック（右から左へ）
    zenkohtei_columns = ['前工程6', '前工程5', '前工程4', '前工程3', '前工程2', '前工程1']
    for col_name in zenkohtei_columns:
        value = row.get(col_name, '').strip()
        if is_not_empty(value):
            row['推定素材'] = value
            return

    kobuban = row.get('カム課_子部番', '').strip()
    if kobuban:
        # カム課_子部番から「Φ数字2桁」を抽出
        # パターン1: Φ(数字)数字 → ()外の数字を優先
        match = re.search(r'Φ\(\d+\)(\d{2})', kobuban)
        if match:
            diameter = match.group(1)
            row['推定素材'] = f'SKD11-DIA{diameter}XL1000'
            return

        # パターン2: 通常のΦ数字2桁
        match = re.search(r'Φ(\d{2})', kobuban)
        if match:
            diameter = match.group(1)
            row['推定素材'] = f'SKD11-DIA{diameter}XL1000'
            return

        # カム課_子部番から「SKD11-DIA数字」を抽出
        match = re.search(r'SKD11-DIA(\d+)', kobuban, re.IGNORECASE)
        if match:
            diameter = match.group(1)
            row['推定素材'] = f'SKD11-DIA{diameter}XL1000'
            return

        # カム課_子部番が「MA-」から始まる場合
        if kobuban.startswith('MA-'):
            row['推定素材'] = kobuban
            return

        # 個別対応マッピング
        for pattern, material in individual_mappings.items():
            if pattern in kobuban:
                row['推定素材'] = material
                return

    # どれにも該当しない場合（最終処理：デフォルト値）
    row['推定素材'] = 'SKD11030085'


def apply_needle_logic(row, needle_data):
    """
    ニードルデータとの突合処理

    加工部番がニードル加工部番と一致した場合、「カム課_工程」に"ﾆｰﾄﾞﾙ"を追記

    Args:
        row: カム課データの1行（dict）
        needle_data: ニードルデータのリスト

    Returns:
        bool: ニードルを追記したかどうか
    """
    kakou_buban = row.get('加工部番', '').strip()
    buhinmei = row.get('部品名', '').strip()
    cam_kotei = row.get('カム課_工程', '').strip()

    if not kakou_buban:
        return False

    # 既にニードルが含まれている場合はスキップ
    if 'ﾆｰﾄﾞﾙ' in cam_kotei:
        return False

    # ニードルデータと突合
    for needle_buban, buhinmei_hosoku, is_wildcard in needle_data:
        # ワイルドカード処理
        if is_wildcard:
            # *より前の部分を取得（前方一致）
            pattern = needle_buban.replace('*', '')
            if not kakou_buban.startswith(pattern):
                continue
        else:
            # 完全一致
            if kakou_buban != needle_buban:
                continue

        # マッチした場合、部品名補足のロジックを適用
        if '除く' in buhinmei_hosoku:
            # 「除く」より前の部品名を取得
            exclude_buhinmei = buhinmei_hosoku.split('除く')[0].strip()

            # 部品名が一致する場合は対象外
            if buhinmei == exclude_buhinmei:
                continue

            # 一致しない場合は処理対象 → ニードルを追記
            if cam_kotei:
                row['カム課_工程'] = cam_kotei + ' ﾆｰﾄﾞﾙ'
            else:
                row['カム課_工程'] = 'ﾆｰﾄﾞﾙ'
            return True

        elif buhinmei_hosoku:
            # 「除く」がなく、部品名補足に文字列がある場合
            # → その部品名のみ処理対象
            if buhinmei == buhinmei_hosoku:
                if cam_kotei:
                    row['カム課_工程'] = cam_kotei + ' ﾆｰﾄﾞﾙ'
                else:
                    row['カム課_工程'] = 'ﾆｰﾄﾞﾙ'
                return True

        else:
            # 部品名補足が空欄の場合 → 全て処理対象
            if cam_kotei:
                row['カム課_工程'] = cam_kotei + ' ﾆｰﾄﾞﾙ'
            else:
                row['カム課_工程'] = 'ﾆｰﾄﾞﾙ'
            return True

    return False


def find_match(cam_row, zenkohtei_indexes):
    """
    カム課データの1行に対して、前工程データとの突合を試みる

    Returns:
        tuple: (条件名, 追加する前工程データのリスト)
    """
    # 突合対象の値
    kakou_buban = cam_row.get('加工部番', '').strip()
    kobuban = cam_row.get('カム課_子部番', '').strip()
    magobuban = cam_row.get('カム課_孫部番', '').strip()

    # 条件定義: (条件名, グループ番号, カム課のカラム値, 前工程のカラム名, 追加する前工程カラムのリスト)
    conditions = [
        # 条件1グループ: 加工部番
        ('条件1-1', 1, kakou_buban, '完成部番', ['前工程1', '前工程2', '前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件1-2', 1, kakou_buban, '前工程1', ['前工程2', '前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件1-3', 1, kakou_buban, '前工程2', ['前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件1-4', 1, kakou_buban, '前工程3', ['前工程4', '前工程5', '前工程6']),
        ('条件1-5', 1, kakou_buban, '前工程4', ['前工程5', '前工程6']),
        ('条件1-6', 1, kakou_buban, '前工程5', ['前工程6']),

        # 条件2グループ: カム課_子部番
        ('条件2-1', 2, kobuban, '完成部番', ['前工程1', '前工程2', '前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件2-2', 2, kobuban, '前工程1', ['前工程2', '前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件2-3', 2, kobuban, '前工程2', ['前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件2-4', 2, kobuban, '前工程3', ['前工程4', '前工程5', '前工程6']),
        ('条件2-5', 2, kobuban, '前工程4', ['前工程5', '前工程6']),
        ('条件2-6', 2, kobuban, '前工程5', ['前工程6']),

        # 条件3グループ: カム課_孫部番
        ('条件3-1', 3, magobuban, '完成部番', ['前工程1', '前工程2', '前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件3-2', 3, magobuban, '前工程1', ['前工程2', '前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件3-3', 3, magobuban, '前工程2', ['前工程3', '前工程4', '前工程5', '前工程6']),
        ('条件3-4', 3, magobuban, '前工程3', ['前工程4', '前工程5', '前工程6']),
        ('条件3-5', 3, magobuban, '前工程4', ['前工程5', '前工程6']),
        ('条件3-6', 3, magobuban, '前工程5', ['前工程6']),
    ]

    # 条件を順に試す
    for condition_name, group_num, cam_value, zen_column, target_columns in conditions:
        if not cam_value:  # カム課の値が空なら次へ
            continue

        # マッチング処理
        matched = False
        zen_data = None

        # "-M1"が含まれる場合は部分一致、含まれない場合は完全一致
        if '-M1' in cam_value:
            # 部分一致: cam_valueが前工程データに含まれるかチェック
            for zen_key in zenkohtei_indexes[zen_column].keys():
                if cam_value in zen_key:
                    matched = True
                    zen_data_list = zenkohtei_indexes[zen_column][zen_key]
                    zen_data = zen_data_list[0]
                    break
        else:
            # 完全一致
            if cam_value in zenkohtei_indexes[zen_column]:
                matched = True
                zen_data_list = zenkohtei_indexes[zen_column][cam_value]
                zen_data = zen_data_list[0]

        if matched:
            # 追加する前工程データを抽出（空欄でないもののみ）
            # 前工程と一緒に単位数分子・単位数分母も抽出
            result_data = {}
            for col_name in target_columns:
                # 前工程Nの値を取得
                value = zen_data.get(col_name, '')
                if is_not_empty(value):
                    result_data[col_name] = value
                else:
                    result_data[col_name] = ''

                # 前工程Nに対応する単位数分子N・単位数分母Nも取得
                # col_name = '前工程1' → '単位数分子1', '単位数分母1'
                if col_name.startswith('前工程'):
                    num = col_name.replace('前工程', '')  # '1', '2', ...
                    bunshi_col = f'単位数分子{num}'
                    bunbo_col = f'単位数分母{num}'

                    bunshi_value = zen_data.get(bunshi_col, '')
                    bunbo_value = zen_data.get(bunbo_col, '')

                    result_data[bunshi_col] = bunshi_value if bunshi_value else ''
                    result_data[bunbo_col] = bunbo_value if bunbo_value else ''

            # マッチした：追加データの有無で条件名を決定（前工程データのみで判定）
            zenkohtei_values = [result_data.get(col, '') for col in target_columns]
            if any(is_not_empty(v) for v in zenkohtei_values):
                # 追加データがある場合：元の条件名
                return condition_name, result_data
            else:
                # 追加データがない場合：条件X-7
                return f'条件{group_num}-7', result_data

    # どの条件にもマッチしない
    return '条件4', {
        '単位数分子1': '',
        '単位数分母1': '',
        '前工程1': '',
        '単位数分子2': '',
        '単位数分母2': '',
        '前工程2': '',
        '単位数分子3': '',
        '単位数分母3': '',
        '前工程3': '',
        '単位数分子4': '',
        '単位数分母4': '',
        '前工程4': '',
        '単位数分子5': '',
        '単位数分母5': '',
        '前工程5': '',
        '単位数分子6': '',
        '単位数分母6': '',
        '前工程6': ''
    }


def apply_skd6g2534_exception(output_row):
    """
    SKD6G2534例外処理

    前工程1～6の一番右のデータが"SKD6G2534"の場合、
    次の項目に 単位数分子="47", 単位数分母="1000", 前工程="SKD11025067" を追加

    Args:
        output_row: 出力行データ（dict）
    """
    # 前工程1～6を右から左へチェック
    zenkohtei_columns = ['前工程6', '前工程5', '前工程4', '前工程3', '前工程2', '前工程1']

    for i, col_name in enumerate(zenkohtei_columns):
        value = output_row.get(col_name, '').strip()
        if is_not_empty(value):
            # 一番右の空欄でないデータを発見
            if value == 'SKD6G2534':
                # 次の項目番号を取得（前工程6 → なし、前工程5 → 6、...、前工程1 → 2）
                current_num = int(col_name.replace('前工程', ''))
                next_num = current_num + 1

                if next_num <= 6:
                    # 次の項目に例外データを追加
                    output_row[f'単位数分子{next_num}'] = '47'
                    output_row[f'単位数分母{next_num}'] = '1000'
                    output_row[f'前工程{next_num}'] = 'SKD11025067'

            # 一番右を見つけたら終了
            break


def main():
    print("=" * 60)
    print("03_5_前工程突合（汎用版）")
    print(f"入力(カム課): {INPUT_CAM}")
    print(f"入力(前工程): {INPUT_ZENKOHTEI}")
    print(f"出力: {OUTPUT_CSV}")
    print("=" * 60)

    # 入力ファイル確認
    if not INPUT_CAM.exists():
        print(f"エラー: カム課ファイルが見つかりません: {INPUT_CAM}")
        return False

    if not INPUT_ZENKOHTEI.exists():
        print(f"エラー: 前工程ファイルが見つかりません: {INPUT_ZENKOHTEI}")
        return False

    # 出力ディレクトリ確認
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 前工程データ読み込み
    zenkohtei_indexes = load_zenkohtei_data(INPUT_ZENKOHTEI)

    # ニードルデータ読み込み
    needle_data = load_needle_data(INPUT_NEEDLE)

    # カム課データを読み込みながら突合
    print("\nカム課データを読み込み、突合中...")

    output_rows = []
    condition_stats = defaultdict(int)
    needle_added_count = 0
    material_stats = defaultdict(int)

    with open(INPUT_CAM, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        original_fieldnames = reader.fieldnames

        # 新しいフィールド名: マッチ条件 + 元のカラム + (単位数分子N + 単位数分母N + 前工程N) × 6 + 推定素材
        new_fieldnames = ['マッチ条件'] + list(original_fieldnames) + [
            '単位数分子1', '単位数分母1', '前工程1',
            '単位数分子2', '単位数分母2', '前工程2',
            '単位数分子3', '単位数分母3', '前工程3',
            '単位数分子4', '単位数分母4', '前工程4',
            '単位数分子5', '単位数分母5', '前工程5',
            '単位数分子6', '単位数分母6', '前工程6',
            '推定素材'
        ]

        for row in reader:
            # 突合処理
            condition_name, zen_data = find_match(row, zenkohtei_indexes)

            # ニードル処理を適用
            needle_added = apply_needle_logic(row, needle_data)
            if needle_added:
                needle_added_count += 1

            # 結果を行に追加（前工程データを先にマージ）
            output_row = {'マッチ条件': condition_name}
            output_row.update(row)
            output_row.update(zen_data)

            # SKD6G2534例外処理を適用
            apply_skd6g2534_exception(output_row)

            # 推定素材を設定
            apply_estimated_material(output_row)

            # 推定素材の分類をカウント
            material = output_row.get('推定素材', '')
            kobuban = output_row.get('カム課_子部番', '').strip()

            # 個別対応マッピング定義（統計用）
            individual_mappings = {
                'SKD7.0X40': 'SKD11040082',
                'SKD7.0X50': 'SKD11050085',
                'SKD9.0X50': 'SKD11030085',
                'SKD6.0X47': 'SKD11047067',
                'SKD6.0X35': 'SKD11035067',
                'SKD6.0X30': 'SKD11030070',
                'SKD5.95X27': 'SKD11027067',
                'SKD5.7X47': 'SKD11047067',
                'SKD4.8X30': 'SKD11030055',
                'SKD4.2X25': 'SKD11025055',
                'SKD25X19': 'SKD11021082',
                'SKD1616': 'SKD11030085',
                'SK5-3X22': 'SKD11030085',
                'SKD6G2540': 'SKD11025067',
                'SKD5Z1236': 'SKD11012050',
                'NC-5': 'SKD11025067'
            }

            if material == 'SKD11030085':
                material_stats['デフォルト値(SKD11030085)'] += 1
            elif material.startswith('MA'):
                material_stats['MA品目'] += 1
            elif material.startswith('SKD11-DIA'):
                # Φ抽出 or SKD11-DIA抽出の判定
                import re
                if kobuban and re.search(r'Φ(\d{2})', kobuban):
                    material_stats['SKD11-DIA(Φ抽出)'] += 1
                elif kobuban and re.search(r'SKD11-DIA(\d+)', kobuban, re.IGNORECASE):
                    material_stats['SKD11-DIA(子部番抽出)'] += 1
                else:
                    material_stats['SKD11-DIA(その他)'] += 1
            elif kobuban and any(pattern in kobuban for pattern in individual_mappings.keys()):
                # 個別対応マッピング
                material_stats['個別対応'] += 1
            else:
                material_stats['前工程から取得'] += 1

            output_rows.append(output_row)
            condition_stats[condition_name] += 1

    # 統計情報
    print(f"\n突合結果:")
    print(f"  総行数: {len(output_rows):,}行")
    for condition_name in sorted(condition_stats.keys()):
        count = condition_stats[condition_name]
        print(f"  {condition_name}: {count:,}件")

    print(f"\nニードル処理結果:")
    print(f"  ニードル追記: {needle_added_count:,}件")

    print(f"\n推定素材設定結果:")
    print(f"  前工程から取得: {material_stats['前工程から取得']:,}件")
    print(f"  SKD11-DIA(Φ抽出): {material_stats['SKD11-DIA(Φ抽出)']:,}件")
    print(f"  SKD11-DIA(子部番抽出): {material_stats['SKD11-DIA(子部番抽出)']:,}件")
    print(f"  MA品目: {material_stats['MA品目']:,}件")
    if material_stats['SKD11-DIA(その他)'] > 0:
        print(f"  SKD11-DIA(その他): {material_stats['SKD11-DIA(その他)']:,}件")
    print(f"  個別対応: {material_stats['個別対応']:,}件")
    print(f"  デフォルト値(SKD11030085): {material_stats['デフォルト値(SKD11030085)']:,}件")

    # CSV出力
    print(f"\n出力中: {OUTPUT_CSV}")
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"\n処理完了")
    print(f"  出力ファイル: {OUTPUT_CSV.name}")
    print(f"  出力行数: {len(output_rows):,}行")
    print(f"  出力列数: {len(new_fieldnames)}列（推定素材を含む）")

    # マッチサンプル表示
    print(f"\nマッチサンプル（条件4以外の最初の5件）:")
    sample_count = 0
    for row in output_rows:
        if row['マッチ条件'] != '条件4':
            print(f"\n  {row['マッチ条件']}: 加工部番={row['加工部番']}")
            print(f"    カム課_子部番={row['カム課_子部番']}, カム課_孫部番={row['カム課_孫部番']}")
            zen_cols = [f"{k}={row.get(k, '')}" for k in ['前工程1', '前工程2', '前工程3', '前工程4', '前工程5', '前工程6'] if row.get(k, '')]
            print(f"    追加: {', '.join(zen_cols) if zen_cols else 'なし'}")
            sample_count += 1
            if sample_count >= 5:
                break

    print("=" * 60)

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
