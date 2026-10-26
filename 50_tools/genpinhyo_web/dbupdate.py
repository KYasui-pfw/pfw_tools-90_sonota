"""夜間処理：データ更新だけを行う（i-Reporter の帳票は作らない）。

タスクスケジューラから `python dbupdate.py` で動かす（ファイル名を変えないこと）。
帳票の作成まで行うなら create_report.py。
"""

import sys
import traceback

from genpin import db, update


def main():
    result = update.run_update()
    print(f"データ更新: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        traceback.print_exc()
        db.log_error(f"dbupdate.py: {error}")
        sys.exit(1)
