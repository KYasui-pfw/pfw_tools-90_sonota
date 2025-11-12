# 事業部別品目マスタ (M0820)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     | rBOM                                                                                                 |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW_ST2                                                                                              |
| 物理テーブル名                 | M0820                                                                                                |
| 論理テーブル名                 | 事業部別品目マスタ                                                                                   |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/10/10                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 品目コード                     | HMCD                           | VARCHAR2(30)                   | Yes (PK) |                      |                                |
|   2 | 管理事業部コード               | KNRBUCD                        | VARCHAR2(3)                    | Yes (PK) |                      |                                |
|   3 | 在庫管理区分                   | ZIKNKBN                        | CHAR(1)                        |          |                      |                                |
|   4 | 有効在庫マイナス許可区分       | VALZIKBN                       | CHAR(1)                        |          |                      |                                |
|   5 | 仕入先コード                   | SRCD                           | VARCHAR2(10)                   |          |                      |                                |
|   6 | 標準仕入単価                   | SRPRICE                        | NUMBER(11, 2)                  |          |                      |                                |
|   7 | 調達区分コード                 | SUPCLSCD                       | VARCHAR2(2)                    |          |                      |                                |
|   8 | 調達部門コード                 | SUPCD                          | VARCHAR2(2)                    |          |                      |                                |
|   9 | 棚番                           | TNBAN                          | VARCHAR2(8)                    |          |                      |                                |
|  10 | 安全在庫数                     | AZQTY                          | NUMBER(10, 2)                  |          |                      |                                |
|  11 | 完成単価区分                   | EDPRICEKBN                     | CHAR(1)                        |          |                      |                                |
|  12 | 月次評価計算区分               | MNHKKBN                        | CHAR(1)                        |          |                      |                                |
|  13 | 在庫評価区分                   | ZIHKKBN                        | CHAR(1)                        |          |                      |                                |
|  14 | 評価単価                       | HKPRICE                        | NUMBER(11, 2)                  |          |                      |                                |
|  15 | 予定単価                       | YTPRICE                        | NUMBER(11, 2)                  |          |                      |                                |
|  16 | 枝番                           | BRANCHNO                       | VARCHAR2(8)                    |          |                      |                                |
|  17 | 営業手配区分                   | EITHKBN                        | CHAR(1)                        |          |                      |                                |
|  18 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  19 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  20 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  21 |                                | UPDTDT                         | DATE                           |          |                      |                                |
|  22 | 在庫補充量                     | ZIREPQTY                       | NUMBER(10, 2)                  | Yes      |                      |                                |
|  23 | 手配納期丸め日数               | SUMMARYDAY                     | NUMBER(2, 0)                   | Yes      |                      |                                |
|  24 | 保管区コード                   | HKNKCD                         | VARCHAR2(10)                   |          |                      |                                |
|  25 | 在庫区分                       | ZAIKOKBN                       | VARCHAR2(2)                    | Yes      |                      |                                |
|  26 | 在庫評価ランクコード           | HKRANKCD                       | VARCHAR2(3)                    | Yes      |                      |                                |
|  27 | 在庫評価ランクコード(過去)     | HKRANKCDHIS                    | VARCHAR2(3)                    |          |                      |                                |
|  28 | 17番処理開始日                 | STDT17                         | DATE                           |          |                      |                                |
|  29 | 17番処理開始時単価             | STPRICE17                      | NUMBER(11, 2)                  |          |                      |                                |
|  30 | 17番処理開始時在庫区分         | ZAIKOKBN17                     | VARCHAR2(2)                    |          |                      |                                |
|  31 | 納入区分                       | NNKBN                          | CHAR(1)                        | Yes      | '2'                  |                                |
|  32 | 納入先コード                   | NNCD                           | VARCHAR2(10)                   |          |                      |                                |
|  33 | 納入場所                       | NNBASHO                        | VARCHAR2(30)                   |          |                      |                                |
|  34 | 自動手配伝票区分               | ATDENKBN                       | CHAR(1)                        | Yes      |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_M0820                       | HMCD,KNRBUCD                             | Yes        |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_M0820                       | PRIMARY KEY                    | HMCD,KNRBUCD                   |
|   2 | SYS_C0062321                   | CHECK                          | "HMCD" IS NOT NULL             |
|   3 | SYS_C0062322                   | CHECK                          | "KNRBUCD" IS NOT NULL          |
|   4 | SYS_C0062323                   | CHECK                          | "ZIKNKBN" IS NOT NULL          |
|   5 | SYS_C0062324                   | CHECK                          | "VALZIKBN" IS NOT NULL         |
|   6 | SYS_C0062325                   | CHECK                          | "AZQTY" IS NOT NULL            |
|   7 | SYS_C0062326                   | CHECK                          | "EDPRICEKBN" IS NOT NULL       |
|   8 | SYS_C0062327                   | CHECK                          | "MNHKKBN" IS NOT NULL          |
|   9 | SYS_C0062328                   | CHECK                          | "ZIHKKBN" IS NOT NULL          |
|  10 | SYS_C0062329                   | CHECK                          | "HKPRICE" IS NOT NULL          |
|  11 | SYS_C0062330                   | CHECK                          | "YTPRICE" IS NOT NULL          |
|  12 | SYS_C0062331                   | CHECK                          | "EITHKBN" IS NOT NULL          |
|  13 | SYS_C0062332                   | CHECK                          | "ZIREPQTY" IS NOT NULL         |
|  14 | SYS_C0062333                   | CHECK                          | "SUMMARYDAY" IS NOT NULL       |
|  15 | SYS_C0062334                   | CHECK                          | "ZAIKOKBN" IS NOT NULL         |
|  16 | SYS_C0062335                   | CHECK                          | "HKRANKCD" IS NOT NULL         |
|  17 | SYS_C0062336                   | CHECK                          | "NNKBN" IS NOT NULL            |
|  18 | SYS_C0062337                   | CHECK                          | "ATDENKBN" IS NOT NULL         |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_M0820_M0050                 | SUPCD                                    | PFW_ST2.M0050                  | SUPCD                                    |              |              |
|   2 | FK_M0820_M0360                 | SUPCLSCD                                 | PFW_ST2.M0360                  | SUPCLSCD                                 |              |              |
|   3 | FK_M0820_M0510                 | KNRBUCD                                  | PFW_ST2.M0510                  | BUCD                                     |              |              |
|   4 | FK_M0820_M0720                 | SRCD                                     | PFW_ST2.M0720                  | SRCD                                     |              |              |
|   5 | FK_M0820_M0720_2               | HKNKCD                                   | PFW_ST2.M0720                  | SRCD                                     |              |              |
|   6 | FK_M0820_M0810                 | HMCD                                     | PFW_ST2.M0810                  | HMCD                                     |              |              |
|   7 | FK_M0820_MK060_1               | HKRANKCD                                 | PFW_ST2.MK060                  | ZAIRANKCD                                |              |              |
|   8 | FK_M0820_MK060_2               | HKRANKCDHIS                              | PFW_ST2.MK060                  | ZAIRANKCD                                |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_D3520_M0820                 | HMCD,KNRBUCD                             | PFW_ST2.D3520                  | HMCD,BUCD                                |              |              |
|   2 | FK_D3590_M0820                 | HMCD,KNRBUCD                             | PFW_ST2.D3590                  | HMCD,BUCD                                |              |              |
|   3 | FK_D4010_M0820_I               | HMCD,KNRBUCD                             | PFW_ST2.D4010                  | HMCD,IBUCD                               |              |              |
|   4 | FK_D4010_M0820_O               | HMCD,KNRBUCD                             | PFW_ST2.D4010                  | HMCD,OBUCD                               |              |              |
|   5 | FK_D4020_M0820                 | HMCD,KNRBUCD                             | PFW_ST2.D4020                  | HMCD,BUCD                                |              |              |



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_M0820                      | Insert,Update                            | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW_ST2                                                                                              |
|   2 | TABLE_NAME                     | M0820                                                                                                |
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
|  20 | NUM_ROWS                       | 158079                                                                                               |
|  21 | BLOCKS                         | 2350                                                                                                 |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 99                                                                                                   |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 158079                                                                                               |
|  33 | LAST_ANALYZED                  | 2025/09/18 7:00:05                                                                                   |
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


