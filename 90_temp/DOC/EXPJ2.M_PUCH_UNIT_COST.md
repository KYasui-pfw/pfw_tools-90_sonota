# 購入単価 (M_PUCH_UNIT_COST)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | EXPJ2                                                                                                |
| 物理テーブル名                 | M_PUCH_UNIT_COST                                                                                     |
| 論理テーブル名                 | 購入単価                                                                                             |
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
|   5 | 購入単価有効開始日付           | EFF_PHASE_IN_DATE              | DATE                           | Yes (PK) |                      |                                |
|   6 | サイズ                         | PUCH_SIZE                      | NUMBER(18, 4)                  | Yes (PK) | 0                    |                                |
|   7 | 購入単価                       | UNIT_COST                      | NUMBER(18, 4)                  |          | 0                    |                                |
|   8 | 購入単価区分                   | UNIT_COST_TYP                  | NUMBER(2, 0)                   |          | 1                    |                                |
|   9 | 購入加工費                     | PROCESSING_COST                | NUMBER(18, 4)                  |          | 0                    |                                |
|  10 | 購入材料費                     | MATERIAL_COST                  | NUMBER(18, 4)                  |          | 0                    |                                |
|  11 | 購入その他経費                 | OTHER_OVERHEADS                | NUMBER(18, 4)                  |          | 0                    |                                |
|  12 | 作成日                         | CREATED_DATE                   | DATE                           |          | sysdate              |                                |
|  13 | 作成者                         | CREATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  14 | 作成プログラム名               | CREATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  15 | 更新日                         | UPDATED_DATE                   | DATE                           |          | sysdate              |                                |
|  16 | 更新者                         | UPDATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  17 | 更新プログラム名               | UPDATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  18 | 更新数                         | MODIFY_COUNT                   | NUMBER                         |          | 0                    |                                |
|  19 | 図面バージョン                 | DRAW_CD_VER                    | VARCHAR2(100)                  |          |                      |                                |
|  20 | 前回単価                       | BEFORE_UNIT_COST               | NUMBER(18, 4)                  |          | 0                    |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | M_PUCH_UNIT_COST_PKY           | COMPANY_CD,VEND_CD,ITEM_CD,EFF_PHASE_IN_DATE,PUCH_SIZE,PLANT_CD | Yes        |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | M_PUCH_UNIT_COST_PKY           | PRIMARY KEY                    | COMPANY_CD,VEND_CD,ITEM_CD,EFF_PHASE_IN_DATE,PUCH_SIZE,PLANT_CD |
|   2 | SYS_C002780782                 | CHECK                          | "PLANT_CD" IS NOT NULL         |
|   3 | SYS_C002780783                 | CHECK                          | "ITEM_CD" IS NOT NULL          |
|   4 | SYS_C002780784                 | CHECK                          | "EFF_PHASE_IN_DATE" IS NOT NULL |
|   5 | SYS_C002780785                 | CHECK                          | "PUCH_SIZE" IS NOT NULL        |
|   6 | SYS_C002780786                 | CHECK                          | "UNIT_COST" IS NOT NULL        |
|   7 | SYS_C002780787                 | CHECK                          | "UNIT_COST_TYP" IS NOT NULL    |
|   8 | SYS_C002780788                 | CHECK                          | "PROCESSING_COST" IS NOT NULL  |
|   9 | SYS_C002780789                 | CHECK                          | "MATERIAL_COST" IS NOT NULL    |
|  10 | SYS_C002780790                 | CHECK                          | "OTHER_OVERHEADS" IS NOT NULL  |
|  11 | SYS_C002780791                 | CHECK                          | "CREATED_DATE" IS NOT NULL     |
|  12 | SYS_C002780792                 | CHECK                          | "CREATED_BY" IS NOT NULL       |
|  13 | SYS_C002780793                 | CHECK                          | "CREATED_PRG_NM" IS NOT NULL   |
|  14 | SYS_C002780794                 | CHECK                          | "UPDATED_DATE" IS NOT NULL     |
|  15 | SYS_C002780795                 | CHECK                          | "UPDATED_BY" IS NOT NULL       |
|  16 | SYS_C002780796                 | CHECK                          | "UPDATED_PRG_NM" IS NOT NULL   |
|  17 | SYS_C002780797                 | CHECK                          | "MODIFY_COUNT" IS NOT NULL     |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | M_PUCH_UNIT_COST_FKY01         | COMPANY_CD,VEND_CD,ITEM_CD,PLANT_CD      | EXPJ2.M_PUCH_UNIT_COST_H       | COMPANY_CD,VEND_CD,ITEM_CD,PLANT_CD      | CASCADE      |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_M_PUCH_UNIT_COST5          | Insert,Update                            | Before row           |                                |
|   2 | TRG_M_PUCH_UNIT_COST_U1        | Insert,Update,Delete                     | After row            |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | EXPJ2                                                                                                |
|   2 | TABLE_NAME                     | M_PUCH_UNIT_COST                                                                                     |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 37748736                                                                                             |
|  12 | NEXT_EXTENT                    |                                                                                                      |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 296327                                                                                               |
|  21 | BLOCKS                         | 4218                                                                                                 |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 96                                                                                                   |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 2000                                                                                                 |
|  33 | LAST_ANALYZED                  | 2025/08/28 9:34:56                                                                                   |
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


