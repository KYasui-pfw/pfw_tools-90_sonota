# 購入単価ヘッダ (M_PUCH_UNIT_COST_H)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | EXPJ2                                                                                                |
| 物理テーブル名                 | M_PUCH_UNIT_COST_H                                                                                   |
| 論理テーブル名                 | 購入単価ヘッダ                                                                                       |
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
|   5 | 購入優先順位                   | PUCH_PRIORITY_REF_NO           | NUMBER(6, 0)                   |          | 1                    |                                |
|   6 | 取引先品目番号                 | VEND_ITEM_CD                   | VARCHAR2(100)                  |          |                      |                                |
|   7 | 作成日                         | CREATED_DATE                   | DATE                           |          | sysdate              |                                |
|   8 | 作成者                         | CREATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|   9 | 作成プログラム名               | CREATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  10 | 更新日                         | UPDATED_DATE                   | DATE                           |          | sysdate              |                                |
|  11 | 更新者                         | UPDATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  12 | 更新プログラム名               | UPDATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  13 | 更新数                         | MODIFY_COUNT                   | NUMBER                         |          | 0                    |                                |
|  14 | 初回品フラグ                   | FIRST_ITEM_FLG                 | NUMBER                         |          | 0                    |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | M_PUCH_UNIT_COST_H_PKY         | COMPANY_CD,VEND_CD,ITEM_CD,PLANT_CD      | Yes        |                                |
|   2 | M_PUCH_UNIT_COST_H_IDX01       | ITEM_CD                                  |            |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | M_PUCH_UNIT_COST_H_PKY         | PRIMARY KEY                    | COMPANY_CD,VEND_CD,ITEM_CD,PLANT_CD |
|   2 | SYS_C002780809                 | CHECK                          | "PLANT_CD" IS NOT NULL         |
|   3 | SYS_C002780810                 | CHECK                          | "ITEM_CD" IS NOT NULL          |
|   4 | SYS_C002780811                 | CHECK                          | "PUCH_PRIORITY_REF_NO" IS NOT NULL |
|   5 | SYS_C002780812                 | CHECK                          | "CREATED_DATE" IS NOT NULL     |
|   6 | SYS_C002780813                 | CHECK                          | "CREATED_BY" IS NOT NULL       |
|   7 | SYS_C002780814                 | CHECK                          | "CREATED_PRG_NM" IS NOT NULL   |
|   8 | SYS_C002780815                 | CHECK                          | "UPDATED_DATE" IS NOT NULL     |
|   9 | SYS_C002780816                 | CHECK                          | "UPDATED_BY" IS NOT NULL       |
|  10 | SYS_C002780817                 | CHECK                          | "UPDATED_PRG_NM" IS NOT NULL   |
|  11 | SYS_C002780818                 | CHECK                          | "MODIFY_COUNT" IS NOT NULL     |
|  12 | SYS_C002780819                 | CHECK                          | "FIRST_ITEM_FLG" IS NOT NULL   |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | M_PUCH_UNIT_COST_H_FKY01       | COMPANY_CD,VEND_CD                       | EXPJ2.M_VEND_CTRL              | COMPANY_CD,VEND_CD                       |              |              |
|   2 | M_PUCH_UNIT_COST_H_FKY02       | PLANT_CD                                 | EXPJ2.M_PLANT                  | PLANT_CD                                 |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | M_PUCH_UNIT_COST_FKY01         | COMPANY_CD,VEND_CD,ITEM_CD,PLANT_CD      | EXPJ2.M_PUCH_UNIT_COST         | COMPANY_CD,VEND_CD,ITEM_CD,PLANT_CD      | CASCADE      |              |



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_M_PUCH_UNIT_COST_H_U1      | Insert,Update,Delete                     | After row            |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | EXPJ2                                                                                                |
|   2 | TABLE_NAME                     | M_PUCH_UNIT_COST_H                                                                                   |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 25165824                                                                                             |
|  12 | NEXT_EXTENT                    |                                                                                                      |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 216302                                                                                               |
|  21 | BLOCKS                         | 2770                                                                                                 |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 86                                                                                                   |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 2000                                                                                                 |
|  33 | LAST_ANALYZED                  | 2025/08/28 9:35:01                                                                                   |
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


