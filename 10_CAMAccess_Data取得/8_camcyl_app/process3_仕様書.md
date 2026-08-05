# process3.py 仕様書

## 概要

EJデータマスターから抽出した完了実績データを、rBOM FastAPI の `/completion` エンドポイントに送信する処理です。

---

## 入力ファイル

```
EJデータマスター_CAMFIN_LOG_ALL.csv
```

- process2.py で Access DB から抽出されたCSV
- 主要カラム: `DATE`, `SRNO`, `FINUM`

---

## 処理フロー

```
1. CSV読み込み（エンコーディング自動判定）
       ↓
2. 日付フィルタリング（過去7日 ～ 翌日の8日間）
       ↓
3. バリデーションチェック（必須フィールド確認）
       ↓
4. 状態チェック（FastAPI /instructions/slip/batch）
   → 未完了/登録エラーのみ送信対象
       ↓
5. 各行を /completion エンドポイントに POST送信
       ↓
6. 処理結果サマリーをログ出力
```

---

## 日付フィルタリング

### 対象期間

```
開始日: 今日 - 7日（1週間前）
終了日: 今日 + 1日（翌日）
合計: 8日間
```

### 目的

過去1週間の実績データのみを対象とし、古いデータの再送信を防止する。

---

## 項目マッピング

CSVカラムからAPIペイロードへの変換:

| CSVカラム | APIフィールド | 説明 |
|-----------|---------------|------|
| DATE | KTEDDT | 完了日（YYYY-MM-DD形式） |
| SRNO | INDNO | 指示番号 |
| （固定値） | lineno | 1 |
| （固定値） | IPTANCD | "SECT1836" |
| FINUM | prdqty | 生産数量 |
| FINUM | ktedqty | 完了数量 |

---

## 送信可能状態チェック

FastAPI `/instructions/slip/batch` エンドポイントで事前に状態を確認し、送信可否を判定します。

### 送信不可条件

| 条件 | 値 | 判定 |
|------|-----|------|
| EDKBN（完納区分） | 1, 2 | 送信不可（完了済み） |
| STATUS | 3, 4, 8 | 送信不可（完了条件） |
| STATUS | 9 | 送信不可（中止） |
| SYORIZUMIKB | 1 | 送信不可（実績登録中） |
| SYORIZUMIKB | 3 | **送信可能**（登録エラー） |
| 上記以外 | - | **送信可能**（未完了） |

### 目的

- 既に完了している指示への重複送信を防止
- 実績登録中（処理中）のデータへの競合を回避
- 登録エラー状態のデータは再送信可能

---

## バリデーション

### 必須フィールド

| フィールド | 説明 |
|------------|------|
| DATE | 完了日 |
| SRNO | 指示番号 |
| FINUM | 数量 |

空値またはNaNの場合はスキップされます。

---

## API送信ペイロード

```python
payload = {
    "KTEDDT": "2026-01-15",     # DATE を YYYY-MM-DD 形式に変換
    "INDNO": "F000012345",      # SRNO
    "lineno": 1,                # 固定値
    "IPTANCD": "SECT1836",      # 固定値
    "prdqty": 10.0,             # FINUM
    "ktedqty": 10.0             # FINUM
}
```

### 送信先

- エンドポイント: `{FASTAPI_BASE_URL}/completion/`
- 認証: `X-API-KEY` ヘッダ（INSERT_API_KEY）

---

## 処理結果サマリー

| カウンタ | 内容 |
|----------|------|
| total | CSV総件数（フィルタリング後） |
| success | 送信成功件数 |
| skip | バリデーションエラー・rBOM未登録 |
| blocked | 送信不可状態により除外 |
| error | API送信失敗 |

---

## 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|--------------|
| PROCESS3_CSV_PATH | 入力CSVパス | /app/output/KakouJisseki/EJデータマスター_CAMFIN_LOG_ALL.csv |
| FASTAPI_BASE_URL | FastAPI URL | http://fastapi-rbom-app:8000 |
| READ_API_KEY | 読み取り用APIキー（状態チェック用） | （必須） |
| INSERT_API_KEY | 書き込み用APIキー（completion送信用） | （必須） |
| LOG_DIR | ログ出力先 | /app/logs |
| LOG_RETENTION_DAYS | ログ保持日数 | 7 |

---

## エラーハンドリング

### rBOMにデータが存在しない場合

```
[15/100] ✗ エラー: rBOMシステムにデータが存在しません (INDNO=F000012345)
[15/100] スキップ: 状態チェック結果なし (INDNO=F000012345)
```

→ ERRORレベル + WARNINGレベルでログ出力し、スキップ

### API送信失敗

```
[20/100] ✗ 送信失敗: INDNO=F000012345, DATE=2026-01-15 - HTTP 500: Internal Server Error
```

→ ERRORレベルでログ出力し、error_countをインクリメント

---

## 実行タイミング

- 15分ごと（cron）
- process1.py と process2.py が両方成功した後に順次実行

---

## ログ出力

- ファイル: `process3_YYYYMMDD.log`
- 場所: `/app/logs/`
- 保持期間: 7日間（自動削除）

### ログ出力例

```
CSVファイルを読み込みました: /app/output/KakouJisseki/EJデータマスター_CAMFIN_LOG_ALL.csv (encoding: utf-8-sig)
データ件数: 5,678行, カラム数: 10
フィルタリング期間: 2026-01-08 ～ 2026-01-16
フィルタリング結果: 5,678行 → 234行 (5,444行除外)

状態チェック開始: 234件の指示データを問い合わせ中...
状態チェック完了: 234件のデータを取得
送信可能: 180件, 送信不可: 54件

データ送信を開始します: 234件
  [1/234] ✓ 送信成功: INDNO=F000012345, DATE=2026-01-15, QTY=10.0 - Success
  [2/234] 除外: 送信不可状態（完了/中止/実績登録中） (INDNO=F000012346)
  ...
```

---

## 関連ファイル

| ファイル | 説明 |
|----------|------|
| process3.py | メイン処理スクリプト |
| logger_config.py | ロギング設定モジュール |
| run_all.sh | 全処理実行ラッパー |
