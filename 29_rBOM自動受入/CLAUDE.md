# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

EJ（旧システム）とrBOM（新システム）間の受入実績データ連携ツール群。

## 実行方法

```bash
# 共有仮想環境
PYTHON="C:/Dev/90_tools/09_EJ_rBOM_マッピング２/venv/Scripts/python.exe"

# スクリプト実行
$PYTHON <script_name>.py
```

## フォルダ構成

### 01_EJ受入→rBOM送信
EJ受入実績をrBOM APIに自動転送する5段階パイプライン。

```
01_EJ受入データ変換.py     → EJ Oracle → CSV抽出
02_送信データ作成.py       → mapping.db突合
03_送信データフィルタリング.py → D3350/D3340で除外判定
04_rBOM受入送信.py         → POST /acceptance/ API送信
run.bat                    → 一括実行
```

詳細は `01_EJ受入→rBOM送信/CLAUDE.md` 参照。

### 02_受入総件数比較
EJとrBOMの受入件数を月別・品目別に比較するツール。

```
01_1_受入件数比較_EJ受入.py   → EJ側: ITEM_CD別にACPT_QTY集計
01_2_受入件数比較_rBOM受入.py → rBOM側: HMCD別にRCVQTY集計
01_3_受入件数比較.py          → 両CSV結合、差分計算
```

出力: `work/01_3_受入件数比較_YYYYMM.csv`（ITEM_CD, EJ数量, rBOM数量, 差分）

## 接続情報

| システム | 接続先 |
|----------|--------|
| EJ Oracle | 172.17.107.102:1521/EXPJ (EXPJ2スキーマ) |
| rBOM API | http://pfw-api |
| mapping.db | Files/mapping.db (26_新マッピングツールからコピー) |

## 関連テーブル

### EJ (Oracle)
- **T_ACPT_RSLT**: 受入実績（PUCH_ODR_CD, ACPT_DATE, ACPT_QTY）
- **T_RLSD_PUCH_ODR**: 発注（ITEM_CD, PUCH_ODR_STS_TYP）

### rBOM (API)
- **D3340**: 発注明細（PONO, LINENO, HMCD, STATUS: 3=一部完納, 4=完納, 8=強制完納）
- **D3350**: 受入ファイル（RCVNO, NOTE）
- **D3360**: 受入明細（RCVNO, RCVDT, RCVQTY, PONO, POLINENO）
