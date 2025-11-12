# 品目仕入単価マスタ (M0910)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     | rBOM                                                                                                 |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW_IT2                                                                                              |
| 物理テーブル名                 | M0910                                                                                                |
| 論理テーブル名                 | 品目仕入単価マスタ                                                                                   |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/09/26                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 品目コード                     | HMCD                           | VARCHAR2(30)                   | Yes (PK) |                      |                                |
|   2 | 管理事業部コード               | BUCD                           | VARCHAR2(3)                    | Yes (PK) |                      |                                |
|   3 | 仕入先コード                   | SRCD                           | VARCHAR2(10)                   | Yes (PK) |                      |                                |
|   4 | 発注単位コード                 | UNIT                           | VARCHAR2(3)                    | Yes (PK) |                      |                                |
|   5 | 単価適用開始日                 | VALDTF                         | DATE                           | Yes (PK) |                      |                                |
|   6 | 境界数量                       | VALQTY                         | NUMBER(10, 2)                  | Yes (PK) |                      |                                |
|   7 | 取引単価                       | PRICE                          | NUMBER(14, 5)                  |          |                      |                                |
|   8 | 備考                           | NOTE                           | VARCHAR2(60)                   |          |                      |                                |
|   9 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  10 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  11 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  12 |                                | UPDTDT                         | DATE                           |          |                      |                                |
|  13 | 初回品検査区分 DEF             | SYOKAIHINKBN                   | CHAR(1)                        | Yes      |                      | 2【1:あり 2:なし】             |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_M0910                       | HMCD,BUCD,SRCD,UNIT,VALDTF,VALQTY        | Yes        |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_M0910                       | PRIMARY KEY                    | HMCD,BUCD,SRCD,UNIT,VALDTF,VALQTY |
|   2 | SYS_C0051853                   | CHECK                          | "HMCD" IS NOT NULL             |
|   3 | SYS_C0051854                   | CHECK                          | "BUCD" IS NOT NULL             |
|   4 | SYS_C0051855                   | CHECK                          | "SRCD" IS NOT NULL             |
|   5 | SYS_C0051856                   | CHECK                          | "UNIT" IS NOT NULL             |
|   6 | SYS_C0051857                   | CHECK                          | "VALDTF" IS NOT NULL           |
|   7 | SYS_C0051858                   | CHECK                          | "VALQTY" IS NOT NULL           |
|   8 | SYS_C0051859                   | CHECK                          | "PRICE" IS NOT NULL            |
|   9 | SYS_C0051860                   | CHECK                          | "SYOKAIHINKBN" IS NOT NULL     |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_M0910_M0510                 | BUCD                                     | PFW_IT2.M0510                  | BUCD                                     |              |              |
|   2 | FK_M0910_M0720                 | SRCD                                     | PFW_IT2.M0720                  | SRCD                                     |              |              |
|   3 | FK_M0910_M0810                 | HMCD                                     | PFW_IT2.M0810                  | HMCD                                     | CASCADE      |              |
|   4 | FK_M0910_S0910                 | UNIT                                     | PFW_IT2.S0910                  | UNIT                                     |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_M0910                      | Insert,Update                            | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW_IT2                                                                                              |
|   2 | TABLE_NAME                     | M0910                                                                                                |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 65536                                                                                                |
|  12 | NEXT_EXTENT                    | 16384                                                                                                |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 9                                                                                                    |
|  21 | BLOCKS                         | 5                                                                                                    |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 77                                                                                                   |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 9                                                                                                    |
|  33 | LAST_ANALYZED                  | 2025/08/29 13:00:29                                                                                  |
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


