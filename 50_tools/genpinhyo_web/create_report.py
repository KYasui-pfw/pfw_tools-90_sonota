"""夜間処理：データ更新のあと、i-Reporter のチェックシート（帳票）が未作成のロットについて作る。

タスクスケジューラから `python create_report.py` で動かす（ファイル名を変えないこと）。
対象は当月〜3か月先のロット。データ更新だけなら dbupdate.py。
"""

import sys
import traceback

from genpin import conmas, db, listing, update


def main():
    result = update.run_update()
    print(f"データ更新: {result}")

    targets = listing.needs_report(listing.load_tag_list_for_window())
    created = conmas.create_reports(targets)
    print(f"i-Reporter 帳票作成: {created}件")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        traceback.print_exc()
        db.log_error(f"create_report.py: {error}")
        sys.exit(1)
