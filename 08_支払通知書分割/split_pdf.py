import os
import re
import fitz  # PyMuPDF
from datetime import datetime
from dotenv import load_dotenv
import shutil

# .envファイルを読み込む
load_dotenv()

INPUT_DIR = os.getenv("INPUT_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
PROCESSED_DIR = os.getenv("PROCESSED_DIR")

def extract_date_from_text(text):
    """
    テキストから「締め日」の日付を抽出する
    フォーマット: 25年09月30日 または 2025年09月30日
    戻り値: (表示用文字列, yyyy_MM_dd形式)
    """
    # 締め日の後の日付パターンを検索（改行を含む）
    # パターン1: 25年09月30日（2桁年）
    pattern1 = r'締め日[\s\n]*(\d{2})年(\d{1,2})月(\d{1,2})日'
    match = re.search(pattern1, text)
    if match:
        year, month, day = match.groups()
        # 2桁の年を4桁に変換（20XXとして扱う）
        full_year = f"20{year}"
        display = f"{full_year}年{month.zfill(2)}月{day.zfill(2)}日"
        folder = f"{full_year}_{month.zfill(2)}_{day.zfill(2)}"
        return (display, folder)

    # パターン2: 2025年09月30日（4桁年）
    pattern2 = r'締め日[\s\n]*(\d{4})年(\d{1,2})月(\d{1,2})日'
    match = re.search(pattern2, text)
    if match:
        year, month, day = match.groups()
        display = f"{year}年{month.zfill(2)}月{day.zfill(2)}日"
        folder = f"{year}_{month.zfill(2)}_{day.zfill(2)}"
        return (display, folder)

    return (None, None)

def extract_supplier_code(text):
    """
    テキストから「登録番号」を抽出する
    フォーマット: (XXXX) ← 括弧内の数字
    """
    pattern = r'\((\d{4})\)'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None

def split_pdf_by_keyword(pdf_path):
    """
    PDFを「支払通知書兼請求書」のキーワードで分割
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    print(f"PDFを読み込みました: {pdf_path}")
    print(f"総ページ数: {total_pages}")

    # 分割ポイントを検出
    split_points = []

    for page_num in range(total_pages):
        page = doc[page_num]
        text = page.get_text()

        # 「支払通知書兼請求書」が含まれているか確認
        if "支払通知書兼請求書" in text:
            print(f"  ページ {page_num + 1}: 「支払通知書兼請求書」を検出")

            # 締め日を抽出
            date_display, date_folder = extract_date_from_text(text)
            if date_display:
                print(f"    締め日: {date_display}")
            else:
                print(f"    警告: 締め日が見つかりませんでした")

            # 登録番号（仕入れ先コード）を抽出
            supplier_code = extract_supplier_code(text)
            if supplier_code:
                print(f"    登録番号: {supplier_code}")
            else:
                print(f"    警告: 登録番号が見つかりませんでした")

            split_points.append({
                'page': page_num,
                'date_display': date_display,
                'date_folder': date_folder,
                'supplier_code': supplier_code
            })

    # 分割ポイントが見つからない場合
    if not split_points:
        print("分割ポイントが見つかりませんでした")
        doc.close()
        return

    # PDFを分割して保存
    for i, split_info in enumerate(split_points):
        start_page = split_info['page']
        end_page = split_points[i + 1]['page'] - 1 if i + 1 < len(split_points) else total_pages - 1

        date_folder = split_info['date_folder'] if split_info['date_folder'] else f"不明_{i+1}"
        supplier_code = split_info['supplier_code'] if split_info['supplier_code'] else "0000"

        # 出力フォルダを作成（締め日/登録番号）
        output_folder = os.path.join(OUTPUT_DIR, date_folder, supplier_code)
        os.makedirs(output_folder, exist_ok=True)

        # 新しいPDFを作成
        new_doc = fitz.open()
        for page_num in range(start_page, end_page + 1):
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        # ファイル名を生成: Syougou_yyyy_MM_dd_XXXX.pdf
        output_filename = f"Syougou_{date_folder}_{supplier_code}.pdf"
        output_path = os.path.join(output_folder, output_filename)

        # PDFを保存
        new_doc.save(output_path)
        new_doc.close()

        print(f"  保存: {output_path} (ページ {start_page + 1} - {end_page + 1})")

    doc.close()
    print("分割処理が完了しました")

def move_to_processed(pdf_path):
    """
    処理済みファイルをprocessedフォルダに移動
    ファイル名に処理日時を追記
    """
    filename = os.path.basename(pdf_path)
    name, ext = os.path.splitext(filename)

    # 現在の日時を取得（YYYYMMDDHHmmss形式）
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # 新しいファイル名
    new_filename = f"{name}_{timestamp}{ext}"
    new_path = os.path.join(PROCESSED_DIR, new_filename)

    # ファイルを移動
    shutil.move(pdf_path, new_path)
    print(f"処理済みファイルを移動: {new_path}")

def main():
    """
    メイン処理
    """
    print("=" * 60)
    print("PDF分割ツール")
    print("=" * 60)

    # inputフォルダ内のPDFファイルを取得
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.pdf')]

    if not pdf_files:
        print("inputフォルダにPDFファイルが見つかりません")
        return

    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        print(f"\n処理開始: {pdf_file}")
        print("-" * 60)

        try:
            # PDF分割
            split_pdf_by_keyword(pdf_path)

            # 処理済みフォルダに移動
            move_to_processed(pdf_path)

        except Exception as e:
            print(f"エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("すべての処理が完了しました")
    print("=" * 60)

if __name__ == "__main__":
    main()
