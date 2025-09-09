# 品目工程マスタ (M0840)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     | rBOM                                                                                                 |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW_IT                                                                                               |
| 物理テーブル名                 | M0840                                                                                                |
| 論理テーブル名                 | 品目工程マスタ                                                                                       |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/08/28                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 品目コード                     | HMCD                           | VARCHAR2(30)                   | Yes (PK) |                      |                                |
|   2 | 番号                           | SEQ                            | NUMBER(4, 0)                   | Yes (PK) |                      |                                |
|   3 | 工順                           | KTSEQ                          | NUMBER(4, 0)                   |          |                      |                                |
|   4 | 工程コード                     | KTCD                           | VARCHAR2(5)                    |          |                      |                                |
|   5 | 仕入先コード                   | SRCD                           | VARCHAR2(10)                   |          |                      |                                |
|   6 | 資源コード                     | SGNCD                          | VARCHAR2(5)                    |          |                      |                                |
|   7 | 段取時間                       | DDTIME                         | NUMBER(4, 0)                   |          |                      |                                |
|   8 | 作業時間                       | SGTIME                         | NUMBER(4, 0)                   |          |                      |                                |
|   9 | リードタイム                   | LDTIME                         | NUMBER(3, 0)                   |          |                      |                                |
|  10 | 仕入単価                       | SRPRICE                        | NUMBER(10, 2)                  |          |                      |                                |
|  11 | 原価科目コード                 | CSBCD                          | VARCHAR2(10)                   |          |                      |                                |
|  12 | 調達区分コード                 | SUPCLSCD                       | VARCHAR2(2)                    |          |                      |                                |
|  13 | 調達部門コード                 | SUPCD                          | VARCHAR2(2)                    |          |                      |                                |
|  14 | 受入検査区分                   | RCVTSTKBN                      | CHAR(1)                        |          |                      |                                |
|  15 | 受入検収区分                   | RCVCHKKBN                      | CHAR(1)                        |          |                      |                                |
|  16 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  17 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  18 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  19 |                                | UPDTDT                         | DATE                           |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_M0840                       | HMCD,SEQ                                 | Yes        |                                |
|   2 | UQ_M0840_1                     | HMCD,KTSEQ                               | 制約       |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_M0840                       | PRIMARY KEY                    | HMCD,SEQ                       |
|   2 | UQ_M0840_1                     | UNIQUE                         | HMCD,KTSEQ                     |
|   3 | SYS_C0046875                   | CHECK                          | "HMCD" IS NOT NULL             |
|   4 | SYS_C0046876                   | CHECK                          | "SEQ" IS NOT NULL              |
|   5 | SYS_C0046877                   | CHECK                          | "KTSEQ" IS NOT NULL            |
|   6 | SYS_C0046878                   | CHECK                          | "KTCD" IS NOT NULL             |
|   7 | SYS_C0046879                   | CHECK                          | "DDTIME" IS NOT NULL           |
|   8 | SYS_C0046880                   | CHECK                          | "SGTIME" IS NOT NULL           |
|   9 | SYS_C0046881                   | CHECK                          | "LDTIME" IS NOT NULL           |
|  10 | SYS_C0046882                   | CHECK                          | "SRPRICE" IS NOT NULL          |
|  11 | SYS_C0046883                   | CHECK                          | "RCVTSTKBN" IS NOT NULL        |
|  12 | SYS_C0046884                   | CHECK                          | "RCVCHKKBN" IS NOT NULL        |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_M0840_M0050                 | SUPCD                                    | PFW_IT.M0050                   | SUPCD                                    |              |              |
|   2 | FK_M0840_M0080                 | CSBCD                                    | PFW_IT.M0080                   | CSBCD                                    |              |              |
|   3 | FK_M0840_M0360                 | SUPCLSCD                                 | PFW_IT.M0360                   | SUPCLSCD                                 |              |              |
|   4 | FK_M0840_M0410                 | KTCD                                     | PFW_IT.M0410                   | KTCD                                     |              |              |
|   5 | FK_M0840_M0430                 | SGNCD                                    | PFW_IT.M0430                   | SGNCD                                    |              |              |
|   6 | FK_M0840_M0720                 | SRCD                                     | PFW_IT.M0720                   | SRCD                                     |              |              |
|   7 | FK_M0840_M0810                 | HMCD                                     | PFW_IT.M0810                   | HMCD                                     |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_M0840                      | Insert,Update                            | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW_IT                                                                                               |
|   2 | TABLE_NAME                     | M0840                                                                                                |
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
|  20 | NUM_ROWS                       | 86                                                                                                   |
|  21 | BLOCKS                         | 5                                                                                                    |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 75                                                                                                   |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 86                                                                                                   |
|  33 | LAST_ANALYZED                  | 2025/08/06 13:00:37                                                                                  |
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


