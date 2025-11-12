import sys
import json
import requests
import os
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

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

    def api_soushin(emno,pono,lineno,ukeirezan,ukeire,kyoseiflg,bikou,po_text):
        
        ###データ更新処理        
        API_KEY = "uV7$flb#AtMK"
        # データを更新するエンドポイントURL
        API_URL = f"http://pfw-api/acceptance/"

        
        # 修正点: float()変換エラーを防ぐため、事前にチェックと変換
        try:
            # ukeireが空文字列の場合は float() 変換でエラーになるため、事前にチェックし 0.0 にする
            ukeire_float = float(ukeire) if ukeire.strip() else 0.0
        except ValueError:
            raise ValueError(f"受入数({ukeire})が不正な数値です。")
        try:
            # linenoが空文字列の場合は int() 変換でエラーになるため、事前にチェックし 0 にする
            lineno_int = float(lineno) if ukeire.strip() else 0
        except ValueError:
            raise ValueError(f"受入数({lineno})が不正な数値です。")

        #完納(2)or一部完納(1)
        edk = 2
        if ukeirezan <= int(ukeire_float): #受入数が受入残以上
            edk = 2
        elif kyoseiflg == "1": #強制完納ON
            edk = 2
        else: #それ以外は一部完納
            edk = 1
        
        # 送信するデータ（Pythonの辞書）
        completion_data = {
            "EDKBN": str(edk),
            "RCVDT": datetime.now().strftime('%Y-%m-%d'), #受入日
            "PONO": str(pono),
            "POLINENO": int(lineno_int),
            "IPTANCD": str(emno),
            "RCVQTY": float(ukeire_float),
            "OKQTY": float(ukeire_float),   
            #"NGQTY": 0,
            "MEINOTE": "(原材料)"+po_text+str(bikou)
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
                raise ValueError("404エラー：接続先が見つかりません")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"エラーが発生しました: {e}")
        if not name:
            # エラーを発生させる
            raise ValueError("エラー:rBOMの担当者コードが見つかりません")
        mapping_work.append({"item": "ukeire_list", "sheet": 1, "cluster": 2, "type": "string", "value": str(name)})
        ### 従業員名取得_End

        # 返却
        #mappings = {"error": "", "mappings": mapping_work}
        #print(json.dumps(mappings))
        # 新実装：mapping.dbから複数行取得
        po_text = jdata[1].replace(' ', '').replace('　', '') #バーコード読み取り
        tenyuuryoku = jdata[2].replace(' ', '').replace('　', '') #手入力
        if tenyuuryoku != "":
            po_text = tenyuuryoku
            
        if po_text == "":
            raise ValueError("エラー: EJ開発番号がありません")

        DB_PATH = r"D:\py\EJ_rBOM_mapping\database\mapping.db"
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rbom_order_no, rbom_line_no, rbom_quantity
            FROM mapping_results
            WHERE ej_order_no = ?
            AND status IN ('済', '済2', '手')
            ORDER BY rbom_m_sequence ASC
        """, (po_text,))

        results = cursor.fetchall()
        conn.close()

        # 結果をリスト形式に変換
        mapping_list = [[row[0], row[1], str(int(row[2]))] for row in results]

        # データが見つからない場合はエラー
        if not mapping_list:
            raise ValueError(f"エラー: EJ発注番号 {po_text} に対応するマッピングデータが見つかりません")

        #シートカウントが必要となったため
        sheet = 1

        for index, inner_list in enumerate(mapping_list):

            #格納のindex番号の調整
            if sheet == 1:
                n = (index + 1) * 8
            else:
                #2枚目（3枚目はないためハード実装）
                m = (index + 1) * 8
                n = (index - 20) * 8
            #トータルのリセット
            total_rcv_qty = 0
            
            # データを取得したいAPIのエンドポイントURL
            API_URL = f"http://pfw-api/orders/slip?pono={inner_list[0]}&lineno={inner_list[1]:03d}"
            headers = {"X-API-KEY": API_KEY}
            data = None  # 初期化を追加
            data_after = None  # 初期化を追加

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

            # 受入が複数行ある場合は、受入数を合計する
            if isinstance(data, list) and data:
                for item in data:
                    # RCVQTYがNoneでないことを確認
                    rcv_qty_val = item.get('RCVQTY')
                    if rcv_qty_val is not None:
                        total_rcv_qty += int(rcv_qty_val)
                bunbo = int(data[0]["THQTY"])
                rbom = f"{inner_list[0]}"+"+"+f"{inner_list[1]:03d}"
                mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n, "type": "string", "value": rbom})
                hinmoku = str(data[0]["HMCD"]) + str(data[0]["SYOKAIHINKBN"])
                if data[0]["SYOKAIHINKBN"] == "1":
                    hinmoku = "★"+hinmoku
                mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+1, "type": "string", "value": hinmoku})
                mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+2, "type": "string", "value": str(data[0]["HMNM"])})
                
                joutai = "未登録"
                if data[0]["STATUS"] in ('3', '4', '8'):  # STATUS 8を完了条件に追加
                    joutai = '受入済'
                elif data[0]["STATUS"] == '9':  # STATUS 9の場合は中止
                    joutai = '中止'
                elif data[0]["SYORIZUMIKB"] == '1':
                    joutai = '受入登録中'
                elif data[0]["SYORIZUMIKB"] == '3':
                    joutai = '登録エラー'
                if joutai =="未登録" or joutai =="登録エラー":
                
                    ukeire_zan = int(bunbo) - int(total_rcv_qty)
                    #更新処理 引数：従業員CD、発注番号、行番号、受入残、受入数、強制完納、備考、EJ発注番号
                    #格納のindex番号の調整
                    if sheet == 1:
                        api_soushin(emno,inner_list[0],f"{inner_list[1]:03d}",ukeire_zan,str(jdata[n-index-1]),str(jdata[n-index]),str(jdata[n-index+1]),po_text)
                    #2枚目（3枚目はないためハード実装）
                    else:
                        api_soushin(emno,inner_list[0],f"{inner_list[1]:03d}",ukeire_zan,str(jdata[m-index-1]),str(jdata[m-index]),str(jdata[m-index+1]),po_text)
                    # 更新後にもう一度取得する
                    # データを取得したいAPIのエンドポイントURL
                    API_URL = f"http://pfw-api/orders/slip?pono={inner_list[0]}&lineno={inner_list[1]:03d}"
                    headers = {"X-API-KEY": API_KEY}
                    try:
                        response = requests.get(API_URL, headers=headers)
                        response.raise_for_status()  # エラーがあればここで例外を発生させる
                        # 成功した場合、JSONデータを取得
                        data_after = response.json()
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 404:
                            raise ValueError(f"404エラー　データが見つかりません")
                    except requests.exceptions.RequestException as e:
                        raise ValueError(f"エラーが発生しました: {e}")
                    joutai = "未登録"
                    if data_after[0]["STATUS"] in ('3', '4', '8'):  # STATUS 8を完了条件に追加
                        joutai = '受入済'
                    elif data_after[0]["STATUS"] == '9':  # STATUS 9の場合は中止
                        joutai = '中止'
                    elif data_after[0]["SYORIZUMIKB"] == '1':
                        joutai = '受入登録中'
                    elif data_after[0]["SYORIZUMIKB"] == '3':
                        joutai = '登録エラー'                    
                else:
                    mapping_work.append({"item": "ukeire_list", "sheet": 1, "cluster": n+7, "type": "string", "value": f"{joutai}につき未更新"})

                meisai = f"{total_rcv_qty}／{bunbo}　{joutai}"
                mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+3, "type": "string", "value": str(meisai)})
            else:
                mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+1, "type": "string", "value": "データ無し"})
                mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+2, "type": "string", "value": ""})
                mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+3, "type": "string", "value": ""})
                mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+4, "type": "string", "value": ""})
            
            #強制完納と備考はいずれの場合もリセット
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+5, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": n+6, "type": "string", "value": ""})
            
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": 252, "type": "string", "value": "1"})

            if sheet == 1 and n == 168:
                sheet = 2
                
        # 取ってきた値をセット
        mappings = {"error": "", "mappings": mapping_work}

        # 返却
        print(json.dumps(mappings))

    if __name__ == "__main__":
        main()

except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
