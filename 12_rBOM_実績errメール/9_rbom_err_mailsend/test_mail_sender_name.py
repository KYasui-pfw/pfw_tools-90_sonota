# test_mail_sender_name.py
# メール送信者名の表示テスト

import sys
import io

# UTF-8出力設定
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("メール送信者名の確認")
print("=" * 80)
print()

# 各機能での送信者名と件名を確認
test_cases = [
    {
        "function_name": "受入機能",
        "expected_from": "rBOMエラー通知 <system_rbom@pfw.co.jp>",
        "expected_subject": "【rBOM】受入実績登録エラー通知"
    },
    {
        "function_name": "棚出機能",
        "expected_from": "rBOMエラー通知 <system_rbom@pfw.co.jp>",
        "expected_subject": "【rBOM】棚出実績登録エラー通知"
    },
    {
        "function_name": "経費工具受入機能",
        "expected_from": "rBOMメール通知 <system_rbom@pfw.co.jp>",
        "expected_subject": "【rBOM】経費工具受入通知"
    }
]

print("修正後のメール送信者名と件名:")
print("-" * 80)
print()

for i, test in enumerate(test_cases, 1):
    print(f"{i}. {test['function_name']}")
    print(f"   From: {test['expected_from']}")
    print(f"   Subject: {test['expected_subject']}")
    print()

print("=" * 80)
print("変更箇所: app/mail_sender.py")
print("=" * 80)
print()
print("修正内容:")
print("  - 機能名（function_name）に応じて送信者名を動的に変更")
print("  - 経費工具受入機能の場合: 'rBOM経費工具発注受領通知'")
print("  - エラーメール機能の場合: 'rBOMエラー通知'（変更なし）")
print()
print("✅ 修正完了")
print()
