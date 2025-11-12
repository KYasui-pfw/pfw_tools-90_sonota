import sys
import json
import requests
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

try:

    ## デバッグ用
    #def df_csv_cnv(df, filename):
    #    # DFをcsvにコンバートして出力
    #    dt_now = datetime.now(timezone(timedelta(hours=9)))  # 日本時刻
    #    csv_name = os.path.dirname(
    #        __file__)+"\\"+dt_now.strftime('%Y%m%d%H%M%S')+"_"+filename+".csv"
    #    # df.to_csv(csv_name,index=False,encoding='CP932')
    #    df.to_csv(csv_name, index=True, encoding='CP932')

    #def text_output(t):
    #    with open(os.path.dirname(__file__)+"\\"+'output.txt', 'w') as f:
    #        f.write(str(t))

    def main():
        # jsonデータ読み取り
        jsonData = json.loads(sys.stdin.readline())
        jdata = jsonData["data"]  # (jsonの中身はdataという固定名称の配列)
        if jdata[0] == '':
            raise ValueError("伝票番号がありません")
        ind_text = jdata[0].replace(' ', '').replace('　', '')
        indno = ind_text[:-4]
        lineno = ind_text[-3:]
        kanryou = float(jdata[1])
        emno = jdata[2].replace(' ', '').replace('　', '')

        data = None  # 初期化を追加
        em_data = None  # 初期化を追加
        name = None # 目的のTANNMを格納する変数


        ###明細再取得処理
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
                raise ValueError(f"404エラー　接続先が見つかりません")
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

        if joutai != "未登録":
            # エラーを発生させる
            raise ValueError("状態が「未登録」ではありません")

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

        ###データ更新処理        
        API_KEY = "uV7$flb#AtMK"
        # データを更新するエンドポイントURL
        API_URL = f"http://pfw-api/completion/"
        # 送信するデータ（Pythonの辞書）
        completion_data = {
            "KTEDDT": datetime.now().strftime('%Y-%m-%d'),
            "INDNO": indno,
            "lineno": lineno,
            #"IPTANCD": "0001",   #★仮設定　実際どうするかは確認
            "IPTANCD": emno,
            "prdqty": float(data[0]["THQTY"]),
            "ktedqty": kanryou,
            "NOTE": "" #ひとまず備考は送信しない
        }
        # リクエストヘッダーにAPIキーを設定
        # APIによってキーの名称が 'X-API-Key', 'Authorization' など異なる場合がある
        headers = {
            "Content-Type": "application/json", # 送信するデータ形式をJSONと指定
            "X-API-KEY": API_KEY                # APIキーをヘッダーに含める
        }
        try:
            # `requests.post` を使ってPOSTリクエストを送信
            # `json`引数に辞書を渡すと、自動的にJSON文字列に変換され送信される
            requests
            session = requests.Session()
            response = session.post(API_URL, headers=headers, json=completion_data)

            # HTTPステータスコードをチェックして、リクエストが成功したか確認
            response.raise_for_status()  # 200番台以外のステータスコードの場合、HTTPErrorを発生させる

            # サーバーからのレスポンスをJSONとして受け取る
            response_data = response.json()

        except requests.exceptions.HTTPError as errh:
            text_output(errh.response.text) 
            raise ValueError(f"HTTPエラー: {errh}")
            # エラーレスポンスの内容を表示する場合
        except requests.exceptions.RequestException as err:
            text_output(str(err)) 
            raise ValueError(f"リクエストエラー: {err}")


        ###もう一度再取得処理（状態を最新に更新する）
        # データを取得したいAPIのエンドポイントURL
        API_KEY = "oG5^Ls%#20yq"
        API_URL = f"http://pfw-api/instructions/slip?indno={indno}&lineno={lineno}"
        headers = {"X-API-KEY": API_KEY}
        try:
            response = requests.get(API_URL, headers=headers)
            response.raise_for_status()  # エラーがあればここで例外を発生させる
            # 成功した場合、JSONデータを取得
            data = response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"404エラー　接続先が見つかりません")
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

        # 取ってきた値をセット
        mappings = {"error": "", "mappings": [
            {"item": "kakoumeisai", "sheet": 1, "cluster": 3, "type": "string", "value": str(name)},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 5, "type": "string", "value": str(data[0]["GETSUJI"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 6, "type": "string", "value": str(data[0]["SEINO"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 7, "type": "string", "value": str(data[0]["SEINO_HMNM"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 8, "type": "string", "value": str(data[0]["HMCD"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 9, "type": "string", "value": str(data[0]["KTCD"])},
            {"item": "kakoumeisai", "sheet": 1, "cluster": 10, "type": "string", "value": str(int(data[0]["THQTY"]))},
            #{"item": "kakoumeisai", "sheet": 1, "cluster": 11, "type": "string", "value": str(int(data[0]["THQTY"]))},　実績登録数は更新しない
            {"item": "kakoumeisai", "sheet": 1, "cluster": 12, "type": "string", "value": joutai}
            ]}

        # 返却
        print(json.dumps(mappings))

    if __name__ == "__main__":
        main()

except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
