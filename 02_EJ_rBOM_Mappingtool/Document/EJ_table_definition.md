# EJシステム - 発注残テーブル定義

## 接続情報
- **データベース**: Oracle Database
- **サーバー**: 172.17.107.102:1521/SN=EXPJ
- **ユーザー/パスワード**: EXPJ2/EXPJ2
- **スキーマ**: EXPJ2
- **テーブル名**: T_RLSD_PUCH_ODR

## 主要カラム（マッピング用）

### T_RLSD_PUCH_ODR (発注残テーブル)
| カラム名 | 論理名 | データ型 | 説明 |
|---------|--------|---------|------|
| PUCH_ODR_CD | 発注番号 | VARCHAR2(100) | PK |
| ITEM_CD | 品目番号 | VARCHAR2(100) | マッピングキー（M_ITEMと結合） |
| PUCH_ODR_QTY | 発注数 | NUMBER(18, 4) | マッピングキー（数量） |
| PUCH_ODR_DLV_DATE | 発注納期 | DATE | 条件抽出用 |
| VEND_CD | 取引先コード | VARCHAR2(100) | |
| COMPANY_CD | 会社コード | VARCHAR2(100) | |
| PLANT_CD | 工場コード | VARCHAR2(8) | |

### M_ITEM (品目マスタテーブル) - 品目名取得用
| カラム名 | 論理名 | データ型 | 説明 |
|---------|--------|---------|------|
| ITEM_CD | 品目番号 | VARCHAR2(100) | PK（結合キー） |
| ITEM_NAME | 品目名 | VARCHAR2(160) | 品目名表示用 |

## 抽出クエリ例（M_ITEMと結合）
```sql
SELECT 
    t.PUCH_ODR_CD,
    t.ITEM_CD,
    m.ITEM_NAME,
    t.PUCH_ODR_QTY,
    t.PUCH_ODR_DLV_DATE,
    t.VEND_CD,
    t.COMPANY_CD,
    t.PLANT_CD
FROM EXPJ2.T_RLSD_PUCH_ODR t
LEFT JOIN EXPJ2.M_ITEM m ON t.ITEM_CD = m.ITEM_CD
WHERE t.PUCH_ODR_DLV_DATE BETWEEN :start_date AND :end_date
ORDER BY t.PUCH_ODR_CD
```

## 注意事項
- 発注残（まだ納品されていない発注データ）
- 品目コード（ITEM_CD）と発注数（PUCH_ODR_QTY）でrBOMシステムとマッピング
- 納期による条件抽出が可能