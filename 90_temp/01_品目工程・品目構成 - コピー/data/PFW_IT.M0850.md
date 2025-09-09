# 品目構成マスタ (M0850)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     | rBOM                                                                                                 |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW_IT                                                                                               |
| 物理テーブル名                 | M0850                                                                                                |
| 論理テーブル名                 | 品目構成マスタ                                                                                       |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/08/28                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 親品目コード                   | OYAHMCD                        | VARCHAR2(30)                   | Yes (PK) |                      |                                |
|   2 | SEQ                            | SEQ                            | NUMBER(5, 0)                   | Yes (PK) |                      |                                |
|   3 | 番号                           | STRNO                          | VARCHAR2(4)                    |          |                      |                                |
|   4 | 親訂正番号                     | OYAREVNO                       | NUMBER(4, 0)                   |          |                      |                                |
|   5 | 表示順序                       | STRSEQ                         | NUMBER(5, 0)                   |          |                      |                                |
|   6 | 子品目コード                   | KOHMCD                         | VARCHAR2(30)                   |          |                      |                                |
|   7 | サイズ_X                       | SIZEX                          | NUMBER(9, 3)                   |          |                      |                                |
|   8 | サイズ_Y                       | SIZEY                          | NUMBER(9, 3)                   |          |                      |                                |
|   9 | サイズ_Z                       | SIZEZ                          | NUMBER(9, 3)                   |          |                      |                                |
|  10 | 形状量                         | SHAPEQTY                       | NUMBER(10, 3)                  |          |                      |                                |
|  11 | 親数量×                       | OYAQTYKBN                      | CHAR(1)                        |          |                      |                                |
|  12 | 親品目数量                     | OYAQTY                         | NUMBER(15, 6)                  |          |                      |                                |
|  13 | 親品目単位コード               | OYAUNIT                        | VARCHAR2(3)                    |          |                      |                                |
|  14 | 子品目数量                     | KOQTY                          | NUMBER(15, 6)                  |          |                      |                                |
|  15 | 子品目単位コード               | KOUNIT                         | VARCHAR2(3)                    |          |                      |                                |
|  16 | 有効小数点桁数                 | VALDEC                         | NUMBER(1, 0)                   |          |                      |                                |
|  17 | 端数処理区分                   | HASUKBN                        | CHAR(1)                        |          |                      |                                |
|  18 | 備考                           | NOTE                           | VARCHAR2(100)                  |          |                      |                                |
|  19 | 訂番記事                       | REVNOTE                        | VARCHAR2(40)                   |          |                      |                                |
|  20 | 訂番日付                       | REVDT                          | DATE                           |          |                      |                                |
|  21 | 訂番担当者コード               | REVTANCD                       | VARCHAR2(8)                    |          |                      |                                |
|  22 | 有効状態                       | VALFLG                         | CHAR(1)                        |          |                      |                                |
|  23 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  24 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  25 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  26 |                                | UPDTDT                         | DATE                           |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_M0850                       | OYAHMCD,SEQ                              | Yes        |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_M0850                       | PRIMARY KEY                    | OYAHMCD,SEQ                    |
|   2 | SYS_C0047890                   | CHECK                          | "OYAHMCD" IS NOT NULL          |
|   3 | SYS_C0047891                   | CHECK                          | "SEQ" IS NOT NULL              |
|   4 | SYS_C0047892                   | CHECK                          | "STRNO" IS NOT NULL            |
|   5 | SYS_C0047893                   | CHECK                          | "OYAREVNO" IS NOT NULL         |
|   6 | SYS_C0047894                   | CHECK                          | "STRSEQ" IS NOT NULL           |
|   7 | SYS_C0047895                   | CHECK                          | "KOHMCD" IS NOT NULL           |
|   8 | SYS_C0047896                   | CHECK                          | "SHAPEQTY" IS NOT NULL         |
|   9 | SYS_C0047897                   | CHECK                          | "OYAQTYKBN" IS NOT NULL        |
|  10 | SYS_C0047898                   | CHECK                          | "OYAQTY" IS NOT NULL           |
|  11 | SYS_C0047899                   | CHECK                          | "OYAUNIT" IS NOT NULL          |
|  12 | SYS_C0047900                   | CHECK                          | "KOQTY" IS NOT NULL            |
|  13 | SYS_C0047901                   | CHECK                          | "KOUNIT" IS NOT NULL           |
|  14 | SYS_C0047902                   | CHECK                          | "VALDEC" IS NOT NULL           |
|  15 | SYS_C0047903                   | CHECK                          | "HASUKBN" IS NOT NULL          |
|  16 | SYS_C0047904                   | CHECK                          | "VALFLG" IS NOT NULL           |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_M0850_M0540                 | REVTANCD                                 | PFW_IT.M0540                   | TANCD                                    |              |              |
|   2 | FK_M0850_M0810_KO              | KOHMCD                                   | PFW_IT.M0810                   | HMCD                                     |              |              |
|   3 | FK_M0850_M0810_OYA             | OYAHMCD                                  | PFW_IT.M0810                   | HMCD                                     |              |              |
|   4 | FK_M0850_S0910_KO              | KOUNIT                                   | PFW_IT.S0910                   | UNIT                                     |              |              |
|   5 | FK_M0850_S0910_OYA             | OYAUNIT                                  | PFW_IT.S0910                   | UNIT                                     |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_M0850                      | Insert,Update                            | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW_IT                                                                                               |
|   2 | TABLE_NAME                     | M0850                                                                                                |
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
|  20 | NUM_ROWS                       | 407015                                                                                               |
|  21 | BLOCKS                         | 5914                                                                                                 |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 91                                                                                                   |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 407015                                                                                               |
|  33 | LAST_ANALYZED                  | 2025/08/06 13:00:35                                                                                  |
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


