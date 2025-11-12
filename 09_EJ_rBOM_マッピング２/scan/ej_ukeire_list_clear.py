import sys
import json
import requests
import os
from typing import List, Dict, Any, Optional

try:

    def main():

        # i-reporterへの返却処理
        mapping_work = []

        sheet = 1
        for i in range(1,22):
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+1, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+2, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+3, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+4, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+5, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+6, "type": "string", "value": ""})

        sheet = 2
        for i in range(1,26):
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+1, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+2, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+3, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+4, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+5, "type": "string", "value": ""})
            mapping_work.append({"item": "ukeire_list", "sheet": sheet, "cluster": i*8+6, "type": "string", "value": ""})

        mappings = {"error": "", "mappings": mapping_work}

        # 返却
        print(json.dumps(mappings))

    if __name__ == "__main__":
        main()

except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
