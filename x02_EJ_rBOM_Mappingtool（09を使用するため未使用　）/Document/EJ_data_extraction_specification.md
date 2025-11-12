# EJシステム データ抽出仕様書

## 概要

EJ-rBOMマッピングツールにおけるEJシステム（Oracle Database）からのデータ抽出の詳細仕様を記述します。

## データベース接続情報

| 項目 | 値 |
|:-----|:---|
| **ホスト** | 172.17.107.102 |
| **ポート** | 1521 |
| **サービス名** | EXPJ |
| **スキーマ** | EXPJ2 |
| **接続ユーザー** | EXPJ2 |
| **パスワード** | EXPJ2 |

## 対象テーブル

### 1. メインテーブル：T_RLSD_PUCH_ODR（発注残）

**テーブル概要**
- **物理名**: EXPJ2.T_RLSD_PUCH_ODR
- **論理名**: 発注残
- **用途**: 発注されているが、まだ受入が完了していない注文データを管理
- **レコード数**: 約767,682件（2025年7月時点）

### 2. 結合テーブル：M_ITEM（品目マスタ）

**テーブル概要**
- **物理名**: EXPJ2.M_ITEM
- **論理名**: 品目
- **用途**: 品目の基本情報（品目名等）を管理
- **結合キー**: ITEM_CD（品目番号）
- **レコード数**: 約1,428,245件（2025年7月時点）

## 抽出SQL仕様

### 実行SQL
```sql
SELECT 
    t.PUCH_ODR_CD as order_no,           -- 発注番号
    t.ITEM_CD as item_code,              -- 品目番号
    m.ITEM_NAME as item_name,            -- 品目名（M_ITEMから取得）
    t.PUCH_ODR_QTY as quantity,          -- 発注数
    t.PUCH_ODR_DLV_DATE as delivery_date,-- 発注納期
    t.VEND_CD as vendor_code,            -- 取引先コード
    t.COMPANY_CD as company_code,        -- 会社コード
    t.PLANT_CD as plant_code             -- 工場コード
FROM EXPJ2.T_RLSD_PUCH_ODR t
LEFT JOIN EXPJ2.M_ITEM m ON t.ITEM_CD = m.ITEM_CD
WHERE t.PUCH_ODR_DLV_DATE >= :start_date 
  AND t.PUCH_ODR_DLV_DATE <= :end_date
  AND t.PUCH_ODR_DLV_DATE >= DATE '2025-07-01'  -- 固定条件
  AND t.ACPT_CMPLT_DATE IS NULL                 -- 受入完了日が空欄のもののみ
ORDER BY t.PUCH_ODR_CD
```

## 抽出条件詳細

### 1. 納期範囲条件（動的パラメータ）
- **条件**: `t.PUCH_ODR_DLV_DATE >= :start_date AND t.PUCH_ODR_DLV_DATE <= :end_date`
- **説明**: ユーザーが画面で指定した納期範囲でフィルタリング
- **パラメータ**: 
  - `:start_date` - 納期開始日（ユーザー指定）
  - `:end_date` - 納期終了日（ユーザー指定）

### 2. システム制限条件（固定）
- **条件**: `t.PUCH_ODR_DLV_DATE >= DATE '2025-07-01'`
- **説明**: データ量削減のため、2025年7月1日以降のデータのみ対象
- **理由**: EJシステムには大量の過去データが存在するため、パフォーマンス向上と処理時間短縮のため

### 3. 受入完了除外条件（固定）
- **条件**: `t.ACPT_CMPLT_DATE IS NULL`
- **説明**: 受入完了日が設定されていないデータのみ対象
- **理由**: 受入完了済みの発注は「発注残」ではないため除外

### 4. 結合条件
- **条件**: `LEFT JOIN EXPJ2.M_ITEM m ON t.ITEM_CD = m.ITEM_CD`
- **説明**: 品目マスタから品目名を取得
- **結合方式**: LEFT JOIN（品目マスタに存在しない品目も含める）

## 取得データ項目

| No. | 項目名 | 物理カラム名 | データ型 | 説明 | 必須 |
|:----|:-------|:-------------|:---------|:-----|:-----|
| 1 | order_no | t.PUCH_ODR_CD | VARCHAR2(100) | 発注番号（主キー） | ✓ |
| 2 | item_code | t.ITEM_CD | VARCHAR2(100) | 品目番号 | - |
| 3 | item_name | m.ITEM_NAME | VARCHAR2(160) | 品目名（結合により取得） | - |
| 4 | quantity | t.PUCH_ODR_QTY | NUMBER(18,4) | 発注数量 | - |
| 5 | delivery_date | t.PUCH_ODR_DLV_DATE | DATE | 発注納期 | - |
| 6 | vendor_code | t.VEND_CD | VARCHAR2(100) | 取引先コード | - |
| 7 | company_code | t.COMPANY_CD | VARCHAR2(100) | 会社コード | - |
| 8 | plant_code | t.PLANT_CD | VARCHAR2(8) | 工場コード | - |

## データ処理仕様

### 1. 日付データ変換
- **対象**: delivery_date（発注納期）
- **変換処理**: `record['delivery_date'].strftime('%Y-%m-%d')`
- **目的**: Pythonの日付オブジェクトを文字列形式に統一

### 2. カラム名変換
- **処理**: `[desc[0].lower() for desc in cursor.description]`
- **目的**: Oracleの大文字カラム名を小文字に統一

### 3. 結果データ形式
- **形式**: 辞書のリスト
- **例**:
```python
[
    {
        'order_no': 'EJ20250701001',
        'item_code': 'ITEM001',
        'item_name': 'サンプル部品A',
        'quantity': 10.0,
        'delivery_date': '2025-08-15',
        'vendor_code': 'V001',
        'company_code': 'C001',
        'plant_code': 'E'
    },
    ...
]
```

## パフォーマンス考慮事項

### 1. インデックス活用
- **T_RLSD_PUCH_ODR_IDX06**: `ITEM_CD, PUCH_ODR_DLV_DATE`
- **効果**: 納期範囲検索とアイテムコード検索の高速化

### 2. データ量制限
- **2025年7月1日以降限定**: 約767,682件中の一部のみ対象
- **受入完了除外**: さらにデータ量を削減

### 3. LEFT JOIN使用
- **理由**: 品目マスタに存在しない品目データも取得対象
- **影響**: 品目名がNULLの場合があることを考慮

## エラーハンドリング

### 1. データベース接続エラー
- **例外**: `cx_Oracle.DatabaseError`
- **メッセージ**: "EJシステムへの接続に失敗しました"

### 2. SQL実行エラー
- **例外**: `cx_Oracle.DatabaseError`
- **メッセージ**: "EJシステムからのデータ取得に失敗しました"

### 3. 日付制限エラー
- **条件**: start_date < date(2025, 7, 1)
- **例外**: `ValueError`
- **メッセージ**: "納期開始日は2025-07-01以降を指定してください。データ量削減のための制限です。"

## 使用モジュール

### 1. EJConnector クラス
- **ファイル**: `data_sources/ej_connector.py`
- **メソッド**: `get_order_backlog(start_date, end_date)`

### 2. 依存ライブラリ
- **cx_Oracle**: Oracle Database接続
- **pandas**: データ処理
- **python-dotenv**: 環境変数管理

## セキュリティ考慮事項

### 1. 接続情報管理
- **環境変数**: .envファイルで管理
- **パラメータバインド**: SQLインジェクション対策

### 2. 接続プール
- **方式**: with文によるコネクション自動クローズ
- **目的**: リソースリーク防止

## 運用上の注意事項

### 1. データ更新頻度
- **T_RLSD_PUCH_ODR**: リアルタイム更新
- **M_ITEM**: 品目マスタメンテナンス時に更新

### 2. システム負荷
- **推奨実行時間**: 業務時間外
- **同時実行制限**: 複数セッション実行時は注意

### 3. データ整合性
- **品目名NULL**: M_ITEMに存在しない品目コードの場合
- **日付フォーマット**: Oracle DATE型からの変換確認