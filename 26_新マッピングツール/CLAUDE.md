# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

新マッピングツールは、発注情報ExcelとrBOMデータのマッピング処理を自動化し、SQLiteデータベースに統合するツールです。

## Commands

```bash
# 仮想環境のPythonを使用（09_EJ_rBOM_マッピング２と共有）
PYTHON="C:/Dev/90_tools/09_EJ_rBOM_マッピング２/venv/Scripts/python.exe"

# メイン処理（サーバーコピー→Excel処理→DB更新）
$PYTHON update_db.py

# Streamlitアプリ（未完成）
$PYTHON -m streamlit run app.py
```

## Architecture

### ファイル構成

| ファイル | 説明 |
|----------|------|
| `update_db.py` | メインスクリプト |
| `excel_processor.py` | Excel処理モジュール（`01_excel_rBOM比較.py`と同期） |
| `app.py` | Streamlit表示アプリ |
| `.env` | 環境変数 |
| `mapping.db` | SQLiteデータベース |

### 処理フロー

```
update_db.py
├── サーバーからExcelをコピー
│   ├── 12月ファイル: \\fsrv24\rbom\発注情報12月EJとrBOM.xlsx
│   └── 11月以前: \\fsrv24\rbom\発注情報EJとrBOM.xlsx
├── 12月ファイルのみexcel_processor.process_december_excel()を実行
│   ├── 前工程横展開CSV取得・結合
│   ├── D3340/D3330/MK020/M0820 APIクエリ
│   ├── Excel自動追記・色分け
│   └── 自動インプット除外判定
├── 処理済みExcelを「発注情報12月EJとrBOM.xlsx」にリネーム
└── SQLiteデータベースにインポート
```

### 同期対象ファイル

以下の2ファイルは同じロジックを持ち、修正時は両方を更新する：

1. `C:\Dev\90_tools\26_新マッピングツール\excel_processor.py`
2. `C:\Dev\90_tools\25_EJ_rBOM_同期\01_excel_rBOM比較.py`

同期が必要な関数:
- `is_numeric_string()` - 数字のみ文字列チェック
- `is_red_background()` - 赤背景チェック
- `mark_auto_input_exclusions()` - 自動インプット除外判定
- `update_excel_from_d3360()` - D3360突合処理

## Database Schema

```sql
CREATE TABLE mapping_results (
    ej_order_no TEXT,
    rbom_order_no TEXT,
    rbom_line_no INTEGER,
    rbom_quantity REAL,
    rbom_m_sequence INTEGER,
    status TEXT,
    period TEXT,
    hmcd TEXT
);
```

## 色分けルール

| 色 | RGB | 意味 |
|----|-----|------|
| 水色 | E0F0FF | D3360突合成功・一致 |
| 赤 | FF6666 | D3360突合成功・不一致（既存数字と新値が異なる） |
| 灰色 | D3D3D3 | 自動インプット除外（工程発注/品目番号なし/取引先不一致/CA・PT） |
| 薄いピンク | FFE4E1 | 自動インプット除外（勘定科目12/33以外） |

## 重要なロジック

### F列上書き判定

```python
def is_numeric_string(value):
    """数字のみの文字列かチェック（00000789→True, 000000011a→False）"""
    if value is None:
        return False
    s = str(value).strip()
    return s != '' and s.isdigit()
```

- F列が数字のみ → スキップ（既存値を維持）
- F列が空欄/テキスト → 上書き可能

### 複数PONO対応

同一発注番号に複数のPONOがある場合、一度でも一致したら水色を維持：

```python
matched_rows = set()
for row in df_csv.iterrows():
    if excel_row in matched_rows:
        continue  # 一致済みはスキップ
    if 一致:
        matched_rows.add(excel_row)
```

## Environment Variables (.env)

```
FILE_DEC=\\fsrv24\rbom\発注情報12月EJとrBOM.xlsx
FILE_NOV=\\fsrv24\rbom\発注情報EJとrBOM.xlsx
API_URL=http://pfw-api
READ_API_KEY=xxxxx
```
