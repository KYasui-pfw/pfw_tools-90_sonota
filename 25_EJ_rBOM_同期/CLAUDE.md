# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

EJ-rBOM同期ツールは、旧EJシステムと新rBOMシステム間の発注データを同期・マッピングするためのツール群です。

## Commands

```bash
# 仮想環境のPythonを使用（依存関係が既にインストール済み）
PYTHON="C:/Dev/90_tools/09_EJ_rBOM_マッピング２/venv/Scripts/python.exe"

# 01: Excel比較・rBOMデータ取得・自動追記
$PYTHON 01_excel_rBOM比較.py

# 02: 自動インプット用CSV作成
$PYTHON 02_自動インプット作成.py
```

## Architecture

### 処理フロー

```
01_excel_rBOM比較.py
├── \\fsrv24\rBOM\発注情報12月EJとrBOM.xlsx をコピー
├── 前工程横展開CSV（3ファイル）をコピー・縦結合
├── D3340/D3330/MK020/M0820 APIクエリでrBOMデータ取得
├── Excel自動追記（F/G列、A列工程コード、B-E/CI-CM列）
├── 色分け（水色=NOTE突合成功、黄色=MK020一致、ピンク=前工程一致、赤=取引先不一致、灰色=自動入力除外）
├── 自動インプット除外判定（F列灰色+除外理由=対象外）
└── 出力: 01_excel_rBOM比較/発注情報_自動追記.xlsx

02_自動インプット作成.py
├── 発注情報_自動追記.xlsx を読み込み
├── フィルタリング（工程空欄、rBOM発注番号空欄、品目番号あり、赤背景除外、CA/PT除外、勘定科目12/33、発注伝票発行日）
├── 抽出データをExcel出力
└── EJ_YYYYMMDD_HHMMSS.csv 出力（RPA用インプット）
```

### 主要API

- **FastAPI Generic Query API**: `http://pfw-api/query`
- **認証**: `X-API-KEY: oG5^Ls%#20yq`
- **対象テーブル**: D3330（発注ヘッダ）、D3340（発注明細）、MK020（工程備考マスタ）、M0820（品目仕入先マスタ）

### Excelカラムマッピング（発注情報.xlsx）

| 列 | 内容 | 備考 |
|----|------|------|
| A | 工程 | MK020.KTCD または 前工程から設定 |
| F | rBOM発注番号 | PONO（0埋め9桁）、水色=NOTE突合一致、赤=NOTE突合不一致、灰色+除外理由=自動入力対象外 |
| G | 行番号 | LINENO（整数） |
| K | 仕入先コード | 赤背景=M0820不一致 |
| L | 品目番号 | MK020/前工程の突合キー |
| CC | 勘定科目 | 原価コード |

### 自動入力除外理由（F列に表示、灰色背景）

| 理由 | 条件 |
|------|------|
| 工程発注 | A列（工程）が空欄でない |
| 品目番号なし | L列（品目番号）が空欄 |
| 取引先不一致(赤) | K列（仕入先コード）が赤背景（M0820と不一致） |
| 取引先CA/PT | K列（仕入先コード）がCA or PT |
| 勘定科目12/33以外 | CC列（勘定科目）が12でも33でもない |

**補足**: 上記いずれかの条件に該当する行はF列が薄い灰色になり、除外理由が記述される
**補足2**: F列が「rBOMで対応する発注の入力をお願いします」の行は、判定前に一旦クリアされて再判定される
**補足3**: NOTE突合処理時、F列が「rBOMで対応する発注の入力をお願いします」の場合も空欄扱いとして更新対象になる

### CSV出力形式（02_自動インプット）

```
仕入先コード,担当者コード,製番,明細備考,品目コード,発注数,希望納期,単価,原価コード
```
- 製番: 固定値 `ZAIKOSEIBAN`
- エンコーディング: Shift_JIS
- 出力先: `\\efdx07\発注登録\発注input`

## Configuration

### 02_自動インプット作成.py のフィルタ条件

```python
# 対象とする発注伝票発行日（変更が必要な場合はここを編集）
TARGET_ISSUE_DATES = [
    "2025/12/15",
    "2025/12/16",
    "2025/12/17",
]
```

## Data Sources

- **入力Excel**: `\\fsrv24\rBOM\発注情報12月EJとrBOM.xlsx`
- **前工程CSV**: `\\172.17.107.102\Purchase\EJ前工程\前工程横展開*.csv`
- **出力先（RPA）**: `\\efdx07\発注登録\発注input`

## 同期対象ファイル

**重要**: 以下の2ファイルは同じロジックを持ち、修正時は両方を更新すること：

1. `C:\Dev\90_tools\25_EJ_rBOM_同期\01_excel_rBOM比較.py` （このファイル）
2. `C:\Dev\90_tools\26_新マッピングツール\excel_processor.py`

同期が必要な関数:
- `is_numeric_string()` - 数字のみ文字列チェック
- `is_red_background()` - 赤背景チェック
- `mark_auto_input_exclusions()` - 自動インプット除外判定
- `update_excel_from_d3360()` - D3360突合処理

## 重要なロジック

### F列上書き判定

- F列が**数字のみ**（例: `00000789`）→ スキップ（既存値を維持）
- F列が空欄/テキスト → 上書き可能
- 判定関数: `is_numeric_string()` で `str.isdigit()` を使用

### 複数PONO対応

同一発注番号に複数のPONOがある場合、一度でも一致したら水色を維持：
- `matched_rows = set()` で一致済み行を追跡
- 一致済み行は後続のPONO処理をスキップ
