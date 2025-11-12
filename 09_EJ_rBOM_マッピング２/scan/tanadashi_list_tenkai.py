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
        with open(os.path.dirname(__file__)+"\\"+'output.txt', 'a') as f:
            f.write(str(t))

    def main():

        # jsonデータ読み取り
        jsonData = json.loads(sys.stdin.readline())
        jdata = jsonData["data"]  # (jsonの中身はdataという固定名称の配列)
        
        # i-reporterへの返却処理
        mapping_work = []

        #APIキーをセット
        API_KEY = "oG5^Ls%#20yq"
        
        ### 従業員名取得_Start
        emno = jdata[0].replace(' ', '').replace('　', '')
        
        em_data = None  # 初期化を追加
        name = None # 目的のTANNMを格納する変数
        
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
        mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": 3, "type": "string", "value": str(name)})
        ### 従業員名取得_End
        # 返却
        #mappings = {"error": "", "mappings": mapping_work}
        #print(json.dumps(mappings))

        ### 処理格納ループStart
        #row = 31 #行
        #manual_row = 29 #手入力する行
        row = 31 #行
        manual_row = 99 #手入力する行
        count = 0


        mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": 0, "type": "string", "value": "1"})
        for i in range(1,row):
        #for i in range(1,15):

            n = (8 * i)

            if jdata[(i*2)-1] == "1":
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+2, "type": "string", "value": "送信対象外"})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+3, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+4, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+5, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+6, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+7, "type": "string", "value": ""})
                continue

            #発注番号が空欄の場合
            if jdata[i*2] == "":
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+2, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+3, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+4, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+5, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+6, "type": "string", "value": ""})
                mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+7, "type": "string", "value": ""})
                       
            #発注番号が空欄以外の場合はAPI通信
            else:
                
                po_text = jdata[i*2].replace(' ', '').replace('　', '')
                alcno = po_text[:-4]
                lineno = po_text[-3:]

                # データを取得したいAPIのエンドポイントURL
                API_URL = f"http://pfw-api/allocations/slip?alcno={alcno}&lineno={lineno}"
                headers = {"X-API-KEY": API_KEY}
                data = None  # 初期化を追加

                try:
                    response = requests.get(API_URL, headers=headers)
                    response.raise_for_status()  # エラーがあればここで例外を発生させる
                    # 成功した場合、JSONデータを取得
                    data = response.json()
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 404:
                        raise ValueError(f"404エラー　データが見つかりません")
                except requests.exceptions.RequestException as e:
                    raise ValueError(f"エラーが発生しました: {e}")
                #if not data:
                #    # エラーを発生させる
                #    raise ValueError("エラー:データが見つかりません。生産管理課に伝票番号＋行番号が有効かどうか確認してください")

                # 受入が複数行ある場合は、受入数を合計する
                if isinstance(data, list) and data:

                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+2, "type": "string", "value": str(data[0]["SEINO"])})
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+3, "type": "string", "value": str(data[0]["HMCD"])})
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+4, "type": "string", "value": str(data[0]["HMNM"])})
                    
                    joutai = "未登録"
                    if data[0]["STATUS"] in ('3', '4', '8'):  # STATUS 8を完了条件に追加
                        joutai = '受入済'
                    elif data[0]["STATUS"] == '9':  # STATUS 9の場合は中止
                        joutai = '中止'
                    elif data[0]["SYORIZUMIKB"] == '1':
                        joutai = '受入登録中'
                    elif data[0]["SYORIZUMIKB"] == '3':
                        joutai = '登録エラー'
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+5, "type": "string", "value": str(joutai)})
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+6, "type": "string", "value": str(data[0]["ALCQTY"])})
                    if data[0]["TNBAN"] is None:
                        mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+7, "type": "string", "value": ""})
                    elif data[0]["BRANCHNO"] is None:
                        mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+7, "type": "string", "value": str(data[0]["TNBAN"])})
                    else:
                        mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+7, "type": "string", "value": str(data[0]["TNBAN"]+"-"+data[0]["BRANCHNO"])})
                else:
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+2, "type": "string", "value": "データ無し"})
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+3, "type": "string", "value": ""})
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+4, "type": "string", "value": ""})
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+5, "type": "string", "value": ""})
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+6, "type": "string", "value": ""})
                    mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": n+7, "type": "string", "value": ""})                

        # 取ってきた値をセット
        mappings = {"error": "", "mappings": mapping_work}

        # 返却
        print(json.dumps(mappings))

    if __name__ == "__main__":
        main()

except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
