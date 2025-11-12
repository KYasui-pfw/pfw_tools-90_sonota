# 品目仕入工程単価マスタ (MK020)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     | rBOM                                                                                                 |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW_IT2                                                                                              |
| 物理テーブル名                 | MK020                                                                                                |
| 論理テーブル名                 | 品目仕入工程単価マスタ                                                                               |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/09/26                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 親品目コード                   | OYAHMCD                        | VARCHAR2(30)                   | Yes (PK) |                      |                                |
|   2 | 工程コード                     | KTCD                           | VARCHAR2(5)                    | Yes (PK) |                      |                                |
|   3 | 管理事業部コード               | BUCD                           | VARCHAR2(3)                    | Yes (PK) |                      |                                |
|   4 | 仕入先コード                   | SRCD                           | VARCHAR2(10)                   | Yes (PK) |                      |                                |
|   5 | 単価適用開始日                 | VALDTF                         | DATE                           | Yes (PK) |                      |                                |
|   6 | 境界数量                       | VALQTY                         | NUMBER(12, 2)                  | Yes (PK) |                      |                                |
|   7 | 取引単価                       | PRICE                          | NUMBER(14, 5)                  | Yes      |                      |                                |
|   8 | 備考                           | NOTE                           | VARCHAR2(60)                   |          |                      |                                |
|   9 | 初回品検査区分                 | SYOKAIHINKBN                   | CHAR(1)                        | Yes      | '2'                  |                                |
|  10 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  11 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  12 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  13 |                                | UPDTDT                         | DATE                           |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_MK020                       | OYAHMCD,KTCD,BUCD,SRCD,VALDTF,VALQTY     | Yes        |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_MK020                       | PRIMARY KEY                    | OYAHMCD,KTCD,BUCD,SRCD,VALDTF,VALQTY |
|   2 | SYS_C0050579                   | CHECK                          | "OYAHMCD" IS NOT NULL          |
|   3 | SYS_C0050580                   | CHECK                          | "KTCD" IS NOT NULL             |
|   4 | SYS_C0050581                   | CHECK                          | "BUCD" IS NOT NULL             |
|   5 | SYS_C0050582                   | CHECK                          | "SRCD" IS NOT NULL             |
|   6 | SYS_C0050583                   | CHECK                          | "VALDTF" IS NOT NULL           |
|   7 | SYS_C0050584                   | CHECK                          | "VALQTY" IS NOT NULL           |
|   8 | SYS_C0050585                   | CHECK                          | "PRICE" IS NOT NULL            |
|   9 | SYS_C0050586                   | CHECK                          | "SYOKAIHINKBN" IS NOT NULL     |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_MK020_M0410                 | KTCD                                     | PFW_IT2.M0410                  | KTCD                                     |              |              |
|   2 | FK_MK020_M0510                 | BUCD                                     | PFW_IT2.M0510                  | BUCD                                     |              |              |
|   3 | FK_MK020_M0720                 | SRCD                                     | PFW_IT2.M0720                  | SRCD                                     |              |              |
|   4 | FK_MK020_M0810                 | OYAHMCD                                  | PFW_IT2.M0810                  | HMCD                                     | CASCADE      |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_MK020                      | Insert,Update                            | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW_IT2                                                                                              |
|   2 | TABLE_NAME                     | MK020                                                                                                |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 65536                                                                                                |
|  12 | NEXT_EXTENT                    | 1048576                                                                                              |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 18                                                                                                   |
|  21 | BLOCKS                         | 8                                                                                                    |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 81                                                                                                   |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 18                                                                                                   |
|  33 | LAST_ANALYZED                  | 2025/09/11 7:00:32                                                                                   |
|  34 | PARTITIONED                    | NO                                                                                                   |
|  35 | IOT_TYPE                       |                                                                                                      |
|  36 | TEMPORARY                      | N                                                                                                    |
|  37 | SECONDARY                      | N                                                                                                    |
|  38 | NESTED                         | NO                                                                                                   |
|  39 | BUFFER_POOL                    | DEFAULT                                                                                              |
|  40 | FLASH_CACHE                    | DEFAULT                                                                                              |
|  41 | CELL_FLASH_CACHE               | DEFAULT                                                                                              |
|  42 | ROW_MOVEMENT                   | DISABLED                                                                                             |
|  43 | GLOBAL_STATS                   | YES                                                                                                  |
|  44 | USER_STATS                     | NO                                                                                                   |
|  45 | DURATION                       |                                                                                                      |
|  46 | SKIP_CORRUPT                   | DISABLED                                                                                             |
|  47 | MONITORING                     | YES                                                                                                  |
|  48 | CLUSTER_OWNER                  |                                                                                                      |
|  49 | DEPENDENCIES                   | DISABLED                                                                                             |
|  50 | COMPRESSION                    | DISABLED                                                                                             |
|  51 | COMPRESS_FOR                   |                                                                                                      |
|  52 | DROPPED                        | NO                                                                                                   |
|  53 | READ_ONLY                      | NO                                                                                                   |
|  54 | SEGMENT_CREATED                | YES                                                                                                  |
|  55 | RESULT_CACHE                   | DEFAULT                                                                                              |
|  56 | CLUSTERING                     | NO                                                                                                   |
|  57 | ACTIVITY_TRACKING              |                                                                                                      |
|  58 | DML_TIMESTAMP                  |                                                                                                      |
|  59 | HAS_IDENTITY                   | NO                                                                                                   |
|  60 | CONTAINER_DATA                 | NO                                                                                                   |
|  61 | INMEMORY                       | DISABLED                                                                                             |
|  62 | INMEMORY_PRIORITY              |                                                                                                      |
|  63 | INMEMORY_DISTRIBUTE            |                                                                                                      |
|  64 | INMEMORY_COMPRESSION           |                                                                                                      |
|  65 | INMEMORY_DUPLICATE             |                                                                                                      |
|  66 | DEFAULT_COLLATION              | USING_NLS_COMP                                                                                       |
|  67 | DUPLICATED                     | N                                                                                                    |
|  68 | SHARDED                        | N                                                                                                    |
|  69 | EXTERNAL                       | NO                                                                                                   |
|  70 | HYBRID                         | NO                                                                                                   |
|  71 | CELLMEMORY                     |                                                                                                      |
|  72 | CONTAINERS_DEFAULT             | NO                                                                                                   |
|  73 | CONTAINER_MAP                  | NO                                                                                                   |
|  74 | EXTENDED_DATA_LINK             | NO                                                                                                   |
|  75 | EXTENDED_DATA_LINK_MAP         | NO                                                                                                   |
|  76 | INMEMORY_SERVICE               |                                                                                                      |
|  77 | INMEMORY_SERVICE_NAME          |                                                                                                      |
|  78 | CONTAINER_MAP_OBJECT           | NO                                                                                                   |
|  79 | MEMOPTIMIZE_READ               | DISABLED                                                                                             |
|  80 | MEMOPTIMIZE_WRITE              | DISABLED                                                                                             |
|  81 | HAS_SENSITIVE_COLUMN           | NO                                                                                                   |
|  82 | ADMIT_NULL                     | NO                                                                                                   |
|  83 | DATA_LINK_DML_ENABLED          | NO                                                                                                   |
|  84 | LOGICAL_REPLICATION            | ENABLED                                                                                              |


