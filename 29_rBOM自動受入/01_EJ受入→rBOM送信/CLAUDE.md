# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

EJ（旧システム）の受入実績をrBOM（新システム）に自動転送する5段階パイプライン。

## 実行方法

```bash
# 共有仮想環境
PYTHON="C:/Dev/90_tools/09_EJ_rBOM_マッピング２/venv/Scripts/python.exe"

# 一括実行
run.bat

# 個別実行
$PYTHON 01_EJ受入データ変換.py
$PYTHON 02_送信データ作成.py
$PYTHON 03_送信データフィルタリング.py
$PYTHON 04_rBOM受入送信.py          # 本番送信
$PYTHON 04_rBOM受入送信.py --dry-run  # テスト実行
```

## 処理フロー

```
01_EJ受入データ変換.py
  入力: EJ Oracle (T_ACPT_RSLT + T_RLSD_PUCH_ODR)
  出力: work/01_EJ受入データ.csv

02_送信データ作成.py
  入力: 01_EJ受入データ.csv、work/mapping.db
  出力: 02_送信データ全件.csv、02_マッピングDBに発注番号無し.csv、02_rBOMに発注無し.csv

03_送信データフィルタリング.py
  入力: 02_送信データ全件.csv、rBOM API (D3350, D3340)
  出力: 03_送信データ.csv、03_除外データ.csv、03_除外データ（要チェック）.csv
  除外: D3350.NOTE一致→受入済み、D3340.STATUS=4or8→完納、STATUS=3→要チェック

04_rBOM受入送信.py
  入力: 03_送信データ.csv
  出力: POST /acceptance/ API送信
```

## 接続情報

| システム | 接続先 |
|----------|--------|
| EJ Oracle | 172.17.107.102:1521/EXPJ (EXPJ2スキーマ) |
| rBOM API | http://pfw-api |
| mapping.db | 26_新マッピングツール または 本番: D:\py\EJ_rBOM_mapping_2\ |

## 関連テーブル

- **D3340**: 発注明細（STATUS: 3=一部完納, 4=完納, 8=強制完納）
- **D3350**: 受入ファイル（NOTE列で重複チェック）
- **mapping_results**: EJ発注番号→rBOM発注番号の対応表
