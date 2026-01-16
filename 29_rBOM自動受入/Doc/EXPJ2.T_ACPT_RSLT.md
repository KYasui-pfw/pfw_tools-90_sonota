# 受入実績 (T_ACPT_RSLT)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | EXPJ2                                                                                                |
| 物理テーブル名                 | T_ACPT_RSLT                                                                                          |
| 論理テーブル名                 | 受入実績                                                                                             |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2026/01/13                                                                                           |
| RDBMS                          | Oracle Database 10g Release 10.2.0.1.0 - Production 10.2.0.1.0                                       |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 発注番号                       | PUCH_ODR_CD                    | VARCHAR2(100)                  | Yes (PK) |                      |                                |
|   2 | 受入回数                       | ACPT_NO                        | NUMBER(6, 0)                   | Yes (PK) | 1                    |                                |
|   3 | 受入数                         | ACPT_QTY                       | NUMBER(18, 4)                  |          | 0                    |                                |
|   4 | 受入日                         | ACPT_DATE                      | DATE                           |          |                      |                                |
|   5 | 単価                           | UNIT_COST                      | NUMBER(18, 4)                  |          | 0                    |                                |
|   6 | 単価区分                       | UNIT_COST_TYP                  | NUMBER(2, 0)                   |          | 1                    |                                |
|   7 | 加工費                         | PROCESSING_COST                | NUMBER(18, 4)                  |          | 0                    |                                |
|   8 | 材料費                         | MATERIAL_COST                  | NUMBER(18, 4)                  |          | 0                    |                                |
|   9 | その他経費                     | OTHER_OVERHEADS                | NUMBER(18, 4)                  |          | 0                    |                                |
|  10 | 値引金額                       | DISC_AMOUNT                    | NUMBER(18, 4)                  |          | 0                    |                                |
|  11 | 受入金額                       | PUCH_ODR_AMOUNT                | NUMBER(18, 4)                  |          | 0                    |                                |
|  12 | 受入状態区分                   | ACPT_STS_TYP                   | NUMBER(2, 0)                   |          | 1                    |                                |
|  13 | 納品書番号                     | DLV_CD                         | VARCHAR2(100)                  |          |                      |                                |
|  14 | 工場コード                     | PLANT_CD                       | VARCHAR2(8)                    |          |                      |                                |
|  15 | 受入場所                       | WH_CD                          | VARCHAR2(100)                  |          |                      |                                |
|  16 | 受入実績備考                   | ACPT_RSLT_COMMENT              | VARCHAR2(320)                  |          |                      |                                |
|  17 | 送り状番号                     | INVOICE_CD                     | VARCHAR2(100)                  |          |                      |                                |
|  18 | レート判定日                   | RATE_JUDGE_DATE                | DATE                           |          |                      |                                |
|  19 | 為替レート                     | EXCH_RATE                      | NUMBER(20, 6)                  |          | 0                    |                                |
|  20 | 税率1                          | TAX_RATE_1                     | NUMBER(18, 4)                  |          | 0                    |                                |
|  21 | 税率2                          | TAX_RATE_2                     | NUMBER(18, 4)                  |          | 0                    |                                |
|  22 | 税率3                          | TAX_RATE_3                     | NUMBER(18, 4)                  |          | 0                    |                                |
|  23 | 本体金額                       | NET_AMOUNT                     | NUMBER(18, 4)                  |          | 0                    |                                |
|  24 | 税額1                          | TAX_AMOUNT_1                   | NUMBER(18, 4)                  |          | 0                    |                                |
|  25 | 税額2                          | TAX_AMOUNT_2                   | NUMBER(18, 4)                  |          | 0                    |                                |
|  26 | 税額3                          | TAX_AMOUNT_3                   | NUMBER(18, 4)                  |          | 0                    |                                |
|  27 | 税込金額                       | AMOUNT_INCLUDE_TAX             | NUMBER(18, 4)                  |          | 0                    |                                |
|  28 | 邦貨金額                       | HOME_CUR_AMOUNT                | NUMBER(18, 4)                  |          | 0                    |                                |
|  29 | 消費税コード                   | TAX_CD                         | VARCHAR2(100)                  |          |                      |                                |
|  30 | 税端数区分                     | TAX_ROUND_TYP                  | NUMBER(2, 0)                   |          | 1                    |                                |
|  31 | メーカロット番号               | VEND_LOT_NO                    | VARCHAR2(100)                  |          |                      |                                |
|  32 | 受入訂正回数                   | ACPT_CRCT_NO                   | NUMBER(6, 0)                   |          | 0                    |                                |
|  33 | 作成日                         | CREATED_DATE                   | DATE                           |          | sysdate              |                                |
|  34 | 作成者                         | CREATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  35 | 作成プログラム名               | CREATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  36 | 更新日                         | UPDATED_DATE                   | DATE                           |          | sysdate              |                                |
|  37 | 更新者                         | UPDATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  38 | 更新プログラム名               | UPDATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  39 | 更新数                         | MODIFY_COUNT                   | NUMBER                         |          | 0                    |                                |
|  40 | 勘定科目                       | ACCT_CD                        | VARCHAR2(96)                   |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | T_ACPT_RSLT_PKY                | PUCH_ODR_CD,ACPT_NO                      | Yes        |                                |
|   2 | T_ACPT_RSLT_IDX01              | WH_CD                                    |            |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | T_ACPT_RSLT_PKY                | PRIMARY KEY                    | PUCH_ODR_CD,ACPT_NO            |
|   2 | SYS_C002845239                 | CHECK                          | "PUCH_ODR_CD" IS NOT NULL      |
|   3 | SYS_C002845240                 | CHECK                          | "ACPT_NO" IS NOT NULL          |
|   4 | SYS_C002845241                 | CHECK                          | "ACPT_QTY" IS NOT NULL         |
|   5 | SYS_C002845242                 | CHECK                          | "UNIT_COST" IS NOT NULL        |
|   6 | SYS_C002845243                 | CHECK                          | "UNIT_COST_TYP" IS NOT NULL    |
|   7 | SYS_C002845244                 | CHECK                          | "PROCESSING_COST" IS NOT NULL  |
|   8 | SYS_C002845245                 | CHECK                          | "MATERIAL_COST" IS NOT NULL    |
|   9 | SYS_C002845246                 | CHECK                          | "OTHER_OVERHEADS" IS NOT NULL  |
|  10 | SYS_C002845247                 | CHECK                          | "DISC_AMOUNT" IS NOT NULL      |
|  11 | SYS_C002845248                 | CHECK                          | "PUCH_ODR_AMOUNT" IS NOT NULL  |
|  12 | SYS_C002845249                 | CHECK                          | "ACPT_STS_TYP" IS NOT NULL     |
|  13 | SYS_C002845250                 | CHECK                          | "PLANT_CD" IS NOT NULL         |
|  14 | SYS_C002845251                 | CHECK                          | "EXCH_RATE" IS NOT NULL        |
|  15 | SYS_C002845252                 | CHECK                          | "TAX_RATE_1" IS NOT NULL       |
|  16 | SYS_C002845253                 | CHECK                          | "TAX_RATE_2" IS NOT NULL       |
|  17 | SYS_C002845254                 | CHECK                          | "TAX_RATE_3" IS NOT NULL       |
|  18 | SYS_C002845255                 | CHECK                          | "NET_AMOUNT" IS NOT NULL       |
|  19 | SYS_C002845256                 | CHECK                          | "TAX_AMOUNT_1" IS NOT NULL     |
|  20 | SYS_C002845257                 | CHECK                          | "TAX_AMOUNT_2" IS NOT NULL     |
|  21 | SYS_C002845258                 | CHECK                          | "TAX_AMOUNT_3" IS NOT NULL     |
|  22 | SYS_C002845259                 | CHECK                          | "AMOUNT_INCLUDE_TAX" IS NOT NULL |
|  23 | SYS_C002845260                 | CHECK                          | "HOME_CUR_AMOUNT" IS NOT NULL  |
|  24 | SYS_C002845261                 | CHECK                          | "TAX_ROUND_TYP" IS NOT NULL    |
|  25 | SYS_C002845262                 | CHECK                          | "ACPT_CRCT_NO" IS NOT NULL     |
|  26 | SYS_C002845263                 | CHECK                          | "CREATED_DATE" IS NOT NULL     |
|  27 | SYS_C002845264                 | CHECK                          | "CREATED_BY" IS NOT NULL       |
|  28 | SYS_C002845265                 | CHECK                          | "CREATED_PRG_NM" IS NOT NULL   |
|  29 | SYS_C002845266                 | CHECK                          | "UPDATED_DATE" IS NOT NULL     |
|  30 | SYS_C002845267                 | CHECK                          | "UPDATED_BY" IS NOT NULL       |
|  31 | SYS_C002845268                 | CHECK                          | "UPDATED_PRG_NM" IS NOT NULL   |
|  32 | SYS_C002845269                 | CHECK                          | "MODIFY_COUNT" IS NOT NULL     |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | T_ACPT_RSLT_FKY01              | PUCH_ODR_CD                              | EXPJ2.T_RLSD_PUCH_ODR          | PUCH_ODR_CD                              | CASCADE      |              |
|   2 | T_ACPT_RSLT_FKY02              | PLANT_CD                                 | EXPJ2.M_PLANT                  | PLANT_CD                                 |              |              |
|   3 | T_ACPT_RSLT_FKY03              | WH_CD                                    | EXPJ2.M_WH                     | WH_CD                                    |              |              |
|   4 | T_ACPT_RSLT_FKY04              | TAX_CD                                   | EXPJ2.M_TAX                    | TAX_CD                                   |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | T_INSPC_RSLT_FKY01             | PUCH_ODR_CD,ACPT_NO                      | EXPJ2.T_INSPC_RSLT             | PUCH_ODR_CD,ACPT_NO                      | CASCADE      |              |
|   2 | T_PART_SUPPLIED_ISSUE_FKY01    | PUCH_ODR_CD,ACPT_NO                      | EXPJ2.T_PART_SUPPLIED_ISSUE    | PUCH_ODR_CD,ACPT_NO                      | CASCADE      |              |



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_T_ACPT_RSLT18              | Insert,Update                            | Before row           |                                |
|   2 | TRG_T_ACPT_RSLT4               | Insert,Update                            | Before row           |                                |
|   3 | TRG_T_ACPT_RSLT_U1             | Insert                                   | After row            |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | EXPJ2                                                                                                |
|   2 | TABLE_NAME                     | T_ACPT_RSLT                                                                                          |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 150994944                                                                                            |
|  12 | NEXT_EXTENT                    |                                                                                                      |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 563928                                                                                               |
|  21 | BLOCKS                         | 12662                                                                                                |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 151                                                                                                  |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 2000                                                                                                 |
|  33 | LAST_ANALYZED                  | 2025/12/23 9:23:35                                                                                   |
|  34 | PARTITIONED                    | NO                                                                                                   |
|  35 | IOT_TYPE                       |                                                                                                      |
|  36 | TEMPORARY                      | N                                                                                                    |
|  37 | SECONDARY                      | N                                                                                                    |
|  38 | NESTED                         | NO                                                                                                   |
|  39 | BUFFER_POOL                    | DEFAULT                                                                                              |
|  40 | ROW_MOVEMENT                   | DISABLED                                                                                             |
|  41 | GLOBAL_STATS                   | YES                                                                                                  |
|  42 | USER_STATS                     | NO                                                                                                   |
|  43 | DURATION                       |                                                                                                      |
|  44 | SKIP_CORRUPT                   | DISABLED                                                                                             |
|  45 | MONITORING                     | YES                                                                                                  |
|  46 | CLUSTER_OWNER                  |                                                                                                      |
|  47 | DEPENDENCIES                   | DISABLED                                                                                             |
|  48 | COMPRESSION                    | DISABLED                                                                                             |
|  49 | DROPPED                        | NO                                                                                                   |


