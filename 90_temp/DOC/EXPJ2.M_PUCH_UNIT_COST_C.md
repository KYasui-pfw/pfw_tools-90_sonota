# 購入単価区分 (M_PUCH_UNIT_COST_C)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | EXPJ2                                                                                                |
| 物理テーブル名                 | M_PUCH_UNIT_COST_C                                                                                   |
| 論理テーブル名                 | 購入単価区分                                                                                         |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/09/26                                                                                           |
| RDBMS                          | Oracle Database 10g Release 10.2.0.1.0 - Production 10.2.0.1.0                                       |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 会社コード                     | COMPANY_CD                     | VARCHAR2(100)                  | Yes (PK) |                      |                                |
|   2 | 取引先コード                   | VEND_CD                        | VARCHAR2(100)                  | Yes (PK) |                      |                                |
|   3 | 工場コード                     | PLANT_CD                       | VARCHAR2(8)                    | Yes (PK) |                      |                                |
|   4 | 品目番号                       | ITEM_CD                        | VARCHAR2(100)                  | Yes (PK) |                      |                                |
|   5 | サイズ                         | PUCH_SIZE                      | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|   6 | 購入単価有効開始日付           | EFF_PHASE_IN_DATE              | DATE                           |          |                      |                                |
|   7 | 購入優先順位                   | PUCH_PRIORITY_REF_NO           | NUMBER(6, 0)                   | Yes      | 1                    |                                |
|   8 | 購入単価                       | UNIT_COST                      | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|   9 | 購入単価区分                   | UNIT_COST_TYP                  | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  10 | 見積ステータス                 | ESTIMATE_STATUS_TYP            | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  11 | 見積回答予定日                 | ESTIMATE_ANSWER_SCH_DATE       | DATE                           |          |                      |                                |
|  12 | 見積回答日                     | ESTIMATE_ANSWER_DATE           | DATE                           |          |                      |                                |
|  13 | 見積有効期限                   | ESTIMATE_VALID_DATE            | DATE                           |          |                      |                                |
|  14 | 図版                           | DRAWING_EDITION                | VARCHAR2(100)                  |          |                      |                                |
|  15 | 図面送付日                     | DRAWING_SEND_DATE              | DATE                           |          |                      |                                |
|  16 | 図面返却日                     | DRAWING_ACPT_DATE              | DATE                           |          |                      |                                |
|  17 | 見積回答書パス                 | ESTIMATE_ANSWER_PATH           | VARCHAR2(4000)                 |          |                      |                                |
|  18 | 作成日                         | CREATED_DATE                   | DATE                           |          | sysdate              |                                |
|  19 | 作成者                         | CREATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  20 | 作成プログラム名               | CREATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  21 | 更新日                         | UPDATED_DATE                   | DATE                           |          | sysdate              |                                |
|  22 | 更新者                         | UPDATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  23 | 更新プログラム名               | UPDATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  24 | 更新数                         | MODIFY_COUNT                   | NUMBER                         |          | 0                    |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | M_PUCH_UNIT_COST_C_PKEY        | COMPANY_CD,VEND_CD,PLANT_CD,ITEM_CD      | Yes        |                                |
|   2 | M_PUCH_UNIT_COST_C_IDX01       | ITEM_CD                                  |            |                                |
|   3 | M_PUCH_UNIT_COST_C_IDX02       | ITEM_CD,PUCH_PRIORITY_REF_NO             |            |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | M_PUCH_UNIT_COST_C_PKEY        | PRIMARY KEY                    | COMPANY_CD,VEND_CD,PLANT_CD,ITEM_CD |
|   2 | SYS_C002780799                 | CHECK                          | "COMPANY_CD" IS NOT NULL       |
|   3 | SYS_C002780800                 | CHECK                          | "VEND_CD" IS NOT NULL          |
|   4 | SYS_C002780801                 | CHECK                          | "PLANT_CD" IS NOT NULL         |
|   5 | SYS_C002780802                 | CHECK                          | "ITEM_CD" IS NOT NULL          |
|   6 | SYS_C002780803                 | CHECK                          | "PUCH_SIZE" IS NOT NULL        |
|   7 | SYS_C002780804                 | CHECK                          | "PUCH_PRIORITY_REF_NO" IS NOT NULL |
|   8 | SYS_C002780805                 | CHECK                          | "UNIT_COST" IS NOT NULL        |
|   9 | SYS_C002780806                 | CHECK                          | "UNIT_COST_TYP" IS NOT NULL    |
|  10 | SYS_C002780807                 | CHECK                          | "ESTIMATE_STATUS_TYP" IS NOT NULL |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_HS_PUCH_UNIT_COST_C        | Insert,Update,Delete                     | After row            |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | EXPJ2                                                                                                |
|   2 | TABLE_NAME                     | M_PUCH_UNIT_COST_C                                                                                   |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 16777216                                                                                             |
|  12 | NEXT_EXTENT                    |                                                                                                      |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 117012                                                                                               |
|  21 | BLOCKS                         | 1888                                                                                                 |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 109                                                                                                  |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 2000                                                                                                 |
|  33 | LAST_ANALYZED                  | 2025/08/28 9:34:59                                                                                   |
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


