# -*- coding: utf-8 -*-
"""
key_repeat.py

CSVを読み込み、行数分だけ特定のキー操作を繰り返す

使い方:
  python key_repeat.py [CSVファイル]

停止方法:
  マウスカーソルを画面左上(0,0)に移動
"""

import sys
import os
import time
import csv
import pyautogui
import pyperclip

# パス設定
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(SCRIPT_DIR, "list.csv")

# 設定
START_DELAY = 10.0    # 開始前の待機時間（秒）
FAILSAFE = True       # マウス(0,0)で停止

# pyautoguiの設定
pyautogui.FAILSAFE = FAILSAFE
pyautogui.PAUSE = 0.1


def check_stop():
    """停止条件チェック"""
    x, y = pyautogui.position()
    if x == 0 and y == 0:
        print("\n停止: マウスが(0,0)に移動されました")
        return True
    return False


def wait_with_check(seconds, description=""):
    """停止チェック付き待機"""
    if description:
        print(f"    待機 {seconds}秒 ({description})")
    for _ in range(int(seconds)):
        if check_stop():
            return False
        time.sleep(1)
    # 残りの端数
    remainder = seconds - int(seconds)
    if remainder > 0:
        time.sleep(remainder)
    return True


def do_key_action(row_num, value):
    """
    キー操作を実行

    Args:
        row_num: 行番号（1始まり）
        value: CSVから読み取った値
    """
    # 9桁にゼロ埋め
    value_padded = value.zfill(9)
    print(f"  値: {value} → {value_padded}")

    # 1. 項目をペースト → 5秒待ち
    print("    1. 項目をペースト")
    pyperclip.copy(value_padded)
    pyautogui.hotkey('ctrl', 'v')
    if not wait_with_check(5):
        return False

    # 2. Tab → 5秒待ち
    print("    2. Tab")
    pyautogui.press('tab')
    if not wait_with_check(5):
        return False

    # 3. 同じ項目をペースト → 5秒待ち
    print("    3. 同じ項目をペースト")
    pyautogui.hotkey('ctrl', 'v')
    if not wait_with_check(5):
        return False

    # 4. Tab → 5秒待ち
    print("    4. Tab")
    pyautogui.press('tab')
    if not wait_with_check(5):
        return False

    # 5. F12 → 300秒待ち
    print("    5. F12")
    pyautogui.press('f12')
    #if not wait_with_check(300, "印刷処理"):
    if not wait_with_check(60, "印刷処理"):
        return False

    # 6. x → 5秒待ち
    print("    6. x")
    pyautogui.press('x')
    if not wait_with_check(5):
        return False

    # 7. Enter → 5秒待ち
    print("    7. Enter")
    pyautogui.press('enter')
    if not wait_with_check(5):
        return False

    # 8. Tab → 5秒待ち
    print("    8. Tab")
    pyautogui.press('tab')
    if not wait_with_check(5):
        return False

    # 9. Enter → 300秒待ち
    print("    9. Enter")
    pyautogui.press('enter')
    #if not wait_with_check(300, "印刷処理"):
    if not wait_with_check(60, "印刷処理"):
        return False

    # 10. Shift+Tab → 5秒待ち
    print("    10. Shift+Tab")
    pyautogui.hotkey('shift', 'tab')
    if not wait_with_check(5):
        return False

    # 11. Shift+Tab → 5秒待ち
    print("    11. Shift+Tab")
    pyautogui.hotkey('shift', 'tab')
    if not wait_with_check(5):
        return False

    return True


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 60)
    print("印刷キー繰り返しスクリプト")
    print("=" * 60)
    print()

    # CSVファイル指定
    csv_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV

    if not os.path.exists(csv_file):
        print(f"エラー: CSVファイルが見つかりません: {csv_file}")
        return 1

    # CSV読み込み（1項目のみ）
    print(f"CSV読み込み: {csv_file}")
    values = []
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)  # ヘッダー読み飛ばし
        print(f"ヘッダー: {header[0]}")
        for row in reader:
            if row:
                values.append(row[0].strip())

    print(f"データ行数: {len(values)}")
    print()

    # 処理時間の見積もり
    time_per_row = 5 + 5 + 5 + 5 + 300 + 5 + 5 + 5 + 300 + 5 + 5  # 645秒
    total_time = time_per_row * len(values)
    print(f"1行あたりの処理時間: 約{time_per_row}秒 ({time_per_row // 60}分{time_per_row % 60}秒)")
    print(f"合計処理時間見積もり: 約{total_time}秒 ({total_time // 3600}時間{(total_time % 3600) // 60}分)")
    print()

    # 開始確認
    print(f"設定:")
    print(f"  開始待機: {START_DELAY}秒")
    print(f"  停止方法: マウスを(0,0)に移動")
    print()
    print(f"{START_DELAY}秒後に開始します...")
    print("対象ウィンドウにフォーカスを移してください")
    print()

    time.sleep(START_DELAY)

    # 実行
    print("開始")
    print("-" * 40)

    success_count = 0
    for i, value in enumerate(values, start=1):
        if check_stop():
            break

        print(f"行 {i}/{len(values)}")

        try:
            result = do_key_action(i, value)
            if result:
                success_count += 1
            else:
                break  # 停止された
        except Exception as e:
            print(f"  エラー: {e}")

    print("-" * 40)
    print(f"完了: {success_count}/{len(values)}件処理")

    return 0


if __name__ == "__main__":
    exit(main())
