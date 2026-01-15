"""
PRNKBN=2でmapping_resultsにないデータ抽出スクリプト

D3330でPRNKBN='2'（発注済）のデータのうち、
mapping_resultsに存在しないものを抽出してCSV出力する
"""

import sqlite3
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# 設定
API_URL = 'http://pfw-api/query'
API_KEY = 'oG5^Ls%#20yq'
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / 'mapping.db'
CHUNK_SIZE = 500


def main():
    headers = {'Content-Type': 'application/json', 'X-API-KEY': API_KEY}

    # 1. D3330でPRNKBN='2'のPONOを取得
    print('Fetching D3330 where PRNKBN=2...')
    all_d3330 = []
    offset = 0
    while True:
        resp = requests.post(API_URL, headers=headers, json={
            'table': 'D3330',
            'where': {'PRNKBN': '2'},
            'limit': 10000,
            'offset': offset
        })
        data = resp.json()
        rows = data.get('rows', [])
        all_d3330.extend(rows)
        print(f'  D3330 offset {offset}: {len(rows)} rows')
        if len(rows) < 10000:
            break
        offset += 10000

    print(f'  D3330 PRNKBN=2 total: {len(all_d3330)} rows')
    df_d3330 = pd.DataFrame(all_d3330)
    pono_list = df_d3330['PONO'].unique().tolist()

    # 2. D3340を取得（PRNKBN=2のPONOでフィルタ）
    print('Fetching D3340...')
    all_d3340 = []
    for i in range(0, len(pono_list), CHUNK_SIZE):
        chunk = pono_list[i:i + CHUNK_SIZE]
        resp = requests.post(API_URL, headers=headers, json={
            'table': 'D3340',
            'where': {'PONO': {'in': chunk}},
            'limit': 10000
        })
        data = resp.json()
        all_d3340.extend(data.get('rows', []))
        print(f'  D3340 chunk {i // CHUNK_SIZE + 1}: {len(data.get("rows", []))} rows')
    print(f'  D3340 total: {len(all_d3340)} rows')

    df_d3340 = pd.DataFrame(all_d3340)

    # 3. D3330とD3340をJOIN（全項目）
    # 重複カラム名にsuffixを付けてマージ（PONOはキーなのでそのまま）
    df_rbom = pd.merge(df_d3340, df_d3330, on='PONO', how='left', suffixes=('', '_D3330'))
    print(f'  Joined D3330+D3340: {len(df_rbom)} rows')

    # STATUS='2'に絞り込み
    df_rbom = df_rbom[df_rbom['STATUS'] == '2']
    print(f'  Filtered STATUS=2: {len(df_rbom)} rows')

    # 4. mapping_resultsを取得
    conn = sqlite3.connect(DB_PATH)
    df_mapping = pd.read_sql_query('SELECT rbom_order_no, rbom_line_no FROM mapping_results', conn)
    conn.close()
    df_mapping['rbom_order_no'] = df_mapping['rbom_order_no'].astype(str)
    df_mapping['rbom_line_no'] = pd.to_numeric(df_mapping['rbom_line_no'], errors='coerce')

    # 5. LEFT JOINしてmapping_resultsにないものを抽出
    df_rbom['PONO'] = df_rbom['PONO'].astype(str)
    df_rbom['LINENO'] = pd.to_numeric(df_rbom['LINENO'], errors='coerce')

    df_result = pd.merge(
        df_rbom,
        df_mapping,
        left_on=['PONO', 'LINENO'],
        right_on=['rbom_order_no', 'rbom_line_no'],
        how='left',
        indicator=True
    )

    # mapping_resultsにないもの
    df_not_in_mapping = df_result[df_result['_merge'] == 'left_only'].drop(
        columns=['_merge', 'rbom_order_no', 'rbom_line_no']
    )
    print(f'  Not in mapping_results: {len(df_not_in_mapping)} rows')

    # 6. カラム名を論理名に変換（テーブル識別プレフィックス付き）
    # D3340（発注明細ファイル）由来のカラム - 全項目
    d3340_rename = {
        'PONO': '発注明細F_発注番号',
        'LINENO': '発注明細F_行番号',
        'TRKBN': '発注明細F_取引区分',
        'SRTNO': '発注明細F_表示順',
        'JUNO': '発注明細F_受注番号',
        'JULINENO': '発注明細F_受注行番号',
        'SEINO': '発注明細F_製番',
        'LISTNO': '発注明細F_リスト番号',
        'VERNO': '発注明細F_発生訂番',
        'STATUS': '発注明細F_状態',
        'RCVTSTKBN': '発注明細F_受入検査区分',
        'RCVCHKKBN': '発注明細F_受入検収区分',
        'RSNCD': '発注明細F_理由コード',
        'HMCNGKBN': '発注明細F_品目変更区分',
        'PARTSKBN': '発注明細F_部品種類',
        'HMCD': '発注明細F_品目コード',
        'HMNM': '発注明細F_品名',
        'HMWNM': '発注明細F_品名全角',
        'MODEL': '発注明細F_型式',
        'MODELW': '発注明細F_型式全角',
        'MAKER': '発注明細F_メーカー',
        'MATERIAL': '発注明細F_材質',
        'PROCESS': '発注明細F_処理名',
        'SHAPEKBN': '発注明細F_形状',
        'SIZEX': '発注明細F_サイズX',
        'SIZEY': '発注明細F_サイズY',
        'SIZEZ': '発注明細F_サイズZ',
        'SHAPEQTY': '発注明細F_形状数',
        'KTCD': '発注明細F_工程コード',
        'DRVDT': '発注明細F_希望納期',
        'RECDT': '発注明細F_回答納期',
        'THQTY': '発注明細F_発注数',
        'THUNIT': '発注明細F_発注単位コード',
        'INQTY': '発注明細F_入数',
        'QTY': '発注明細F_発注量',
        'UNIT': '発注明細F_単位コード',
        'WEIGHT': '発注明細F_品目重量',
        'TWEIGHT': '発注明細F_品目総重量',
        'KPKBN': '発注明細F_仮単価区分',
        'KPRSNCD': '発注明細F_仮単価理由コード',
        'PCMMTDT': '発注明細F_単価決定予定日',
        'PKBN': '発注明細F_単価区分',
        'PRICE': '発注明細F_単価',
        'AMOUNT': '発注明細F_金額',
        'TAXKBN': '発注明細F_消費税区分',
        'TAX': '発注明細F_消費税',
        'PRNKBN': '発注明細F_注文書発行区分',
        'PRNDT': '発注明細F_注文書発行日',
        'NKFLG': '発注明細F_入荷フラグ',
        'NNKBN': '発注明細F_納入区分',
        'NNCD': '発注明細F_納入先コード',
        'NNBASHO': '発注明細F_納入場所',
        'SEIBUCD': '発注明細F_製造事業部コード',
        'SBCD': '発注明細F_勘定科目コード',
        'CSBCD': '発注明細F_原価科目コード',
        'PRNO': '発注明細F_発注指示番号',
        'PRLINENO': '発注明細F_発注指示行番号',
        'NOTE': '発注明細F_備考',
        'POSTRECDTM': '発注明細F_POST回答日時',
        'POSTRECTAN': '発注明細F_POST回答担当者',
        'POSTRECNOTE': '発注明細F_POST回答備考',
        'NOTAXAMT': '発注明細F_税抜金額',
        'TAXRATE': '発注明細F_消費税率',
        'KGZEIFLG': '発注明細F_軽減税率対象フラグ',
        'INSTID': '発注明細F_登録者ID',
        'INSTDT': '発注明細F_登録日時',
        'UPDTID': '発注明細F_更新者ID',
        'UPDTDT': '発注明細F_更新日時',
    }
    # D3330（発注ファイル）由来のカラム - 全項目（_D3330 suffix付きも含む）
    d3330_rename = {
        'CNGCNT': '発注_版数',
        'PODT': '発注_発注日',
        'SRCD': '発注_仕入先コード',
        'SRTANNM': '発注_仕入先担当者',
        'SHCD': '発注_支払先コード',
        'SHBUCD': '発注_支払事業部コード',
        'DEPTCD': '発注_部門コード',
        'TANCD': '発注_担当者コード',
        'SUPCD': '発注_調達部門コード',
        'IPTANCD': '発注_入力担当者コード',
        'TAXKBN_D3330': '発注_消費税計算区分',
        'AMOUNT_D3330': '発注_伝票金額合計',
        'TAX_D3330': '発注_伝票消費税合計',
        'NOTE_D3330': '発注_摘要',
        'RCGTANCD': '発注_承認担当者コード',
        'RCGDT': '発注_承認日付',
        'PRNKBN_D3330': '発注_注文書発行区分',
        'PRNDT_D3330': '発注_注文書発行日',
        'PRNCNGCNT': '発注_注文書発行時版数',
        'SETNOUKBN': '発注_セット商品区分',
        'INDQTY': '発注_指示数',
        'ESTRNO': '発注_見積依頼番号',
        'SEIAUTONO': '発注_自動手配番号',
        'POSTKBN': '発注_POST連携区分',
        'POSTOUTKBN': '発注_POST出力区分',
        'ZUMENIMGKBN': '発注_図面イメージ送付',
        'RCGST': '発注_承認状態',
        'INSTID_D3330': '発注_登録者ID',
        'INSTDT_D3330': '発注_登録日時',
        'UPDTID_D3330': '発注_更新者ID',
        'UPDTDT_D3330': '発注_更新日時',
    }
    # カラム名変換
    rename_map = {**d3340_rename, **d3330_rename}
    df_not_in_mapping = df_not_in_mapping.rename(columns=rename_map)

    # 7. CSV出力
    output_file = SCRIPT_DIR / f'prnkbn2_not_in_mapping_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    df_not_in_mapping.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'Output: {output_file}')

    # サマリー
    print(f'\nSummary:')
    print(f'  D3330 PRNKBN=2: {len(all_d3330)}')
    print(f'  D3340 details: {len(all_d3340)}')
    print(f'  Not in mapping_results: {len(df_not_in_mapping)}')


if __name__ == '__main__':
    main()
