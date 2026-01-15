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

# Streamlitアプリ（EJ⇔rBOM発注マッピング情報）
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

## Excel列マッピング

### 通常ファイル（Sheet1）
| 列インデックス | 項目名 | DB列 |
|---------------|--------|------|
| 0（A列） | EJ発注番号 | ej_order_no |
| 3（D列） | EJ品目コード | hmcd |
| 5（F列） | EJ数 | rbom_quantity |
| 10（K列） | rBOM発注番号+行番号 | 分割→rbom_order_no, rbom_line_no |

### 12月ファイル（T_RLSD_PUCH_ODR）
| 列インデックス | 項目名 | DB列 |
|---------------|--------|------|
| 5（F列） | rBOM発注番号 | rbom_order_no（必須） |
| 6（G列） | 行番号 | rbom_line_no |
| 7（H列） | 連番号 | ej_order_no |
| 11（L列） | 品目番号 | hmcd（フォールバック） |
| 12（M列） | 発注数 | rbom_quantity（フォールバック） |
| 89（CL列） | rBOM品目CD | hmcd |
| 90（CM列） | rBOM発注数 | rbom_quantity |

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

## Streamlitアプリ（app.py）

### タブ構成

| タブ | 機能 |
|-----|------|
| タブ1 | 2025年12月15日以降の発注マッピング表示 |
| タブ2 | 2025年11月以前の発注残マッピング表示 |
| タブ3 | EJ⇔rBOM項目チェック（6項目の不一致検出） |
| タブ4 | rBOM重複発注チェック |

### タブ3：項目チェックのロジック

EJとrBOMの以下6項目を比較し、不一致を検出：
- 担当者コード、仕入先コード、品目コード、希望納期、発注数、単価

**品目コード不一致のMK020照合**:
1. EJ品目コード ≠ rBOM品目コードの行を抽出
2. MK020テーブルから`OYAHMCD`と`NOTE`を取得
3. `rBOM品目コード = MK020.OYAHMCD`でJOIN
4. JOINした`NOTE`の中に`EJ品目コード`が含まれていれば → 不一致から除外

### データソース

| ソース | 用途 |
|--------|------|
| mapping.db (SQLite) | マッピング結果 |
| EJ Oracle (172.17.107.102:1521/EXPJ) | T_RLSD_PUCH_ODR |
| rBOM API (http://pfw-api/query) | D3330, D3340, D3360, MK020 |

## Environment Variables (.env)

```
FILE_DEC=\\fsrv24\rbom\発注情報12月EJとrBOM.xlsx
FILE_NOV=\\fsrv24\rbom\発注情報EJとrBOM.xlsx
API_URL=http://pfw-api
READ_API_KEY=xxxxx
```
