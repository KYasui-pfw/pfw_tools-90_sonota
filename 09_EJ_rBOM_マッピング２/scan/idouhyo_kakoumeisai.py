import sys
import json
import requests
import os
from typing import List, Dict, Any, Optional

try:

    # デバッグ用
    def df_csv_cnv(df, filename):
        # DFをcsvにコンバートして出力
        dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
        csv_name = os.path.dirname(
            __file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_"+filename+".csv"
        # df.to_csv(csv_name,index=False,encoding='CP932')
        df.to_csv(csv_name, index=True, encoding='CP932')

    def text_output(t):
        with open(os.path.dirname(__file__)+"\\"+'output.txt', 'w') as f:
            f.write(str(t))

    def main():

        # jsonデータ読み取り
        jsonData = json.loads(sys.stdin.readline())
        jdata = jsonData["data"]  # (jsonの中身はdataという固定名称の配列)

        if jdata[0] == '':
            raise ValueError("伝票番号がありません")

        ind_text = jdata[0].replace(' ', '').replace('　', '')
        indno = ind_text[:-4]
        lineno = ind_text[-3:]
        emno = jdata[1].replace(' ', '').replace('　', '')

        data = None  # 初期化を追加
        em_data = None  # 初期化を追加
        name = None # 目的のTANNMを格納する変数

        #APIキーをセット
        API_KEY = "oG5^Ls%#20yq"
        # データを取得したいAPIのエンドポイントURL
        API_URL = f"http://pfw-api/instructions/slip?indno={indno}&lineno={lineno}"
        headers = {"X-API-KEY": API_KEY}
        try:
            response = requests.get(API_URL, headers=headers)
            response.raise_for_status()  # エラーがあればここで例外を発生させる
            # 成功した場合、JSONデータを取得
            data = response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"404エラー　データが見つかりません")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"エラーが発生しました: {e}")
        if not data:
            # エラーを発生させる
            raise ValueError("エラー:データが見つかりません。生産管理課に伝票番号＋行番号が有効かどうか確認してください")

        joutai = "未登録"
        if data[0]["EDKKBN"] in ('1', '2'):  # 完納区分が設定されている場合
            joutai = '実績登録済'
        elif data[0]["STATUS"] in ('3', '4', '8'):  # STATUS 8を完了条件に追加
            joutai = '実績登録済'
        elif data[0]["STATUS"] == '9':  # STATUS 9の場合は中止
            joutai = '中止'
        elif data[0]["SYORIZUMIKB"] == '1':
            joutai = '実績登録中'
        elif data[0]["SYORIZUMIKB"] == '9':
            joutai = '登録エラー'

        # 従業員コード
        API_URL = f"http://pfw-api/employees/"
        headers = {"X-API-KEY": API_KEY}
        try:
            response = requests.get(API_URL, headers=headers)
            response.raise_for_status()  # エラーがあればここで例外を発生させる
            # 成功した場合、JSONデータを取得
            em_data = response.json()

            # dataリストの各要素(item)を調べる
            for item in em_data:
              # itemの中の'TANCD'が'0001'と一致するか確認
              if item['TANCD'] == emno:
                # 一致した場合、そのitemの'TANNM'を取得
                name = item['TANNM']
                # 目的のデータが見つかったのでループを抜ける
                break
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"404エラー　接続先が見つかりません")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"エラーが発生しました: {e}")
        if not name:
            # エラーを発生させる
            raise ValueError("エラー:rBOMの担当者コードが見つかりません")

        # 取ってきた値をセット
        mappings = {"error": "", "mappings": [
            {"item": "kakoumeisai", "sheet": 1, "cluster": 3, "type": "string", "value": str(name)},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 5, "type": "string", "value": str(data[0]["GETSUJI"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 6, "type": "string", "value": str(data[0]["SEINO"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 7, "type": "string", "value": str(data[0]["SEINO_HMNM"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 8, "type": "string", "value": str(data[0]["HMCD"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 9, "type": "string", "value": str(data[0]["KTCD"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 10, "type": "string", "value": str(int(data[0]["THQTY"]))},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 11, "type": "string", "value": str(int(data[0]["THQTY"]))},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 12, "type": "string", "value": joutai}
            ]}

        # 返却
        print(json.dumps(mappings))

    if __name__ == "__main__":
        main()

except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
