import sys
import json
import requests
import os
from typing import List, Dict, Any, Optional

try:

    def main():

        # i-reporterへの返却処理
        mapping_work = []
        for i in range(8, 256):
            mapping_work.append({"item": "tanadashi_list", "sheet": 1, "cluster": i, "type": "string", "value": ""})
        mappings = {"error": "", "mappings": mapping_work}

        # 返却
        print(json.dumps(mappings))

    if __name__ == "__main__":
        main()

except Exception as e:
    mappings = {"error": "Pythonでエラー：" + str(e)}
    print(json.dumps(mappings))
