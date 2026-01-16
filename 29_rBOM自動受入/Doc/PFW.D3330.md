# 発注ファイル (D3330)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW                                                                                                  |
| 物理テーブル名                 | D3330                                                                                                |
| 論理テーブル名                 | 発注ファイル                                                                                         |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/12/15                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 発注番号                       | PONO                           | VARCHAR2(15)                   | Yes (PK) |                      |                                |
|   2 | 版数                           | CNGCNT                         | NUMBER(2, 0)                   | Yes      |                      |                                |
|   3 | 発注日                         | PODT                           | DATE                           | Yes      |                      |                                |
|   4 | 仕入先コード                   | SRCD                           | VARCHAR2(10)                   | Yes      |                      |                                |
|   5 | 仕入先担当者                   | SRTANNM                        | VARCHAR2(20)                   |          |                      |                                |
|   6 | 支払先コード                   | SHCD                           | VARCHAR2(10)                   | Yes      |                      |                                |
|   7 | 支払事業部コード               | SHBUCD                         | VARCHAR2(3)                    | Yes      |                      |                                |
|   8 | 部門コード                     | DEPTCD                         | VARCHAR2(8)                    | Yes      |                      |                                |
|   9 | 担当者コード                   | TANCD                          | VARCHAR2(8)                    | Yes      |                      |                                |
|  10 | 調達部門コード                 | SUPCD                          | VARCHAR2(2)                    |          |                      |                                |
|  11 | 入力担当者コード               | IPTANCD                        | VARCHAR2(8)                    | Yes      |                      |                                |
|  12 | 消費税計算区分                 | TAXKBN                         | CHAR(1)                        | Yes      |                      |                                |
|  13 | 伝票金額合計                   | AMOUNT                         | NUMBER(10, 0)                  | Yes      |                      |                                |
|  14 | 伝票消費税合計                 | TAX                            | NUMBER(9, 0)                   | Yes      |                      |                                |
|  15 | 摘要                           | NOTE                           | VARCHAR2(60)                   |          |                      |                                |
|  16 | 承認担当者コード               | RCGTANCD                       | VARCHAR2(8)                    |          |                      |                                |
|  17 | 承認日付                       | RCGDT                          | DATE                           |          |                      |                                |
|  18 | 注文書発行区分                 | PRNKBN                         | CHAR(1)                        | Yes      |                      |                                |
|  19 | 注文書発行日                   | PRNDT                          | DATE                           |          |                      |                                |
|  20 | 注文書発行時版数               | PRNCNGCNT                      | NUMBER(2, 0)                   | Yes      |                      |                                |
|  21 | セット商品区分                 | SETNOUKBN                      | CHAR(1)                        |          |                      |                                |
|  22 | 指示数                         | INDQTY                         | NUMBER(3, 0)                   |          |                      |                                |
|  23 | 見積依頼番号                   | ESTRNO                         | VARCHAR2(15)                   |          |                      |                                |
|  24 | 自動手配番号                   | SEIAUTONO                      | VARCHAR2(15)                   |          |                      |                                |
|  25 | POST連携区分                   | POSTKBN                        | CHAR(1)                        | Yes      |                      |                                |
|  26 | POST出力区分                   | POSTOUTKBN                     | CHAR(1)                        | Yes      |                      |                                |
|  27 | 図面ｲﾒｰｼﾞ送付                  | ZUMENIMGKBN                    | CHAR(1)                        | Yes      |                      |                                |
|  28 | 承認状態                       | RCGST                          | CHAR(1)                        | Yes      | '1'                  |                                |
|  29 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  30 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  31 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  32 |                                | UPDTDT                         | DATE                           |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_D3330                       | PONO                                     | Yes        |                                |
|   2 | IDX_D3330_SRCD                 | SRCD                                     |            |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_D3330                       | PRIMARY KEY                    | PONO                           |
|   2 | SYS_C0099169                   | CHECK                          | "PONO" IS NOT NULL             |
|   3 | SYS_C0099170                   | CHECK                          | "CNGCNT" IS NOT NULL           |
|   4 | SYS_C0099171                   | CHECK                          | "PODT" IS NOT NULL             |
|   5 | SYS_C0099172                   | CHECK                          | "SRCD" IS NOT NULL             |
|   6 | SYS_C0099173                   | CHECK                          | "SHCD" IS NOT NULL             |
|   7 | SYS_C0099174                   | CHECK                          | "SHBUCD" IS NOT NULL           |
|   8 | SYS_C0099175                   | CHECK                          | "DEPTCD" IS NOT NULL           |
|   9 | SYS_C0099176                   | CHECK                          | "TANCD" IS NOT NULL            |
|  10 | SYS_C0099177                   | CHECK                          | "IPTANCD" IS NOT NULL          |
|  11 | SYS_C0099178                   | CHECK                          | "TAXKBN" IS NOT NULL           |
|  12 | SYS_C0099179                   | CHECK                          | "AMOUNT" IS NOT NULL           |
|  13 | SYS_C0099180                   | CHECK                          | "TAX" IS NOT NULL              |
|  14 | SYS_C0099181                   | CHECK                          | "PRNKBN" IS NOT NULL           |
|  15 | SYS_C0099182                   | CHECK                          | "PRNCNGCNT" IS NOT NULL        |
|  16 | SYS_C0099183                   | CHECK                          | "POSTKBN" IS NOT NULL          |
|  17 | SYS_C0099184                   | CHECK                          | "POSTOUTKBN" IS NOT NULL       |
|  18 | SYS_C0099185                   | CHECK                          | "ZUMENIMGKBN" IS NOT NULL      |
|  19 | SYS_C0099186                   | CHECK                          | "RCGST" IS NOT NULL            |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_D3330_M0050                 | SUPCD                                    | PFW.M0050                      | SUPCD                                    |              |              |
|   2 | FK_D3330_M0510_SH              | SHBUCD                                   | PFW.M0510                      | BUCD                                     |              |              |
|   3 | FK_D3330_M0520                 | DEPTCD                                   | PFW.M0520                      | DEPTCD                                   |              |              |
|   4 | FK_D3330_M0540                 | TANCD                                    | PFW.M0540                      | TANCD                                    |              |              |
|   5 | FK_D3330_M0540_IP              | IPTANCD                                  | PFW.M0540                      | TANCD                                    |              |              |
|   6 | FK_D3330_M0540_RCG             | RCGTANCD                                 | PFW.M0540                      | TANCD                                    |              |              |
|   7 | FK_D3330_M0720                 | SRCD                                     | PFW.M0720                      | SRCD                                     |              |              |
|   8 | FK_D3330_M0730                 | SHCD                                     | PFW.M0730                      | SHCD                                     |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_D3330                      | Insert,Update                            | Before row           |                                |
|   2 | TRG_D3330_D0940                | Delete                                   | Before row           |                                |
|   3 | TRG_D3330_UPDT                 | Insert,Update,Delete                     | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW                                                                                                  |
|   2 | TABLE_NAME                     | D3330                                                                                                |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 57344                                                                                                |
|  12 | NEXT_EXTENT                    | 16384                                                                                                |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 1584                                                                                                 |
|  21 | BLOCKS                         | 35                                                                                                   |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 148                                                                                                  |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 1584                                                                                                 |
|  33 | LAST_ANALYZED                  | 2025/11/13 7:00:18                                                                                   |
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


