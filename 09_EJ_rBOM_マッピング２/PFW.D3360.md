# 受入明細ファイル (D3360)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW                                                                                                  |
| 物理テーブル名                 | D3360                                                                                                |
| 論理テーブル名                 | 受入明細ファイル                                                                                     |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/12/05                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 受入番号                       | RCVNO                          | VARCHAR2(15)                   | Yes (PK) |                      |                                |
|   2 | 行番号                         | LINENO                         | NUMBER(3, 0)                   | Yes (PK) |                      |                                |
|   3 | 取引区分                       | TRKBN                          | CHAR(1)                        | Yes      |                      |                                |
|   4 | 発注番号                       | PONO                           | VARCHAR2(15)                   | Yes      |                      |                                |
|   5 | 発注行番号                     | POLINENO                       | NUMBER(3, 0)                   | Yes      |                      |                                |
|   6 | 状態                           | STATUS                         | CHAR(1)                        | Yes      |                      |                                |
|   7 | 受入検査区分                   | RCVTSTKBN                      | CHAR(1)                        | Yes      |                      |                                |
|   8 | 受入検収区分                   | RCVCHKKBN                      | CHAR(1)                        | Yes      |                      |                                |
|   9 | 完納区分                       | EDKBN                          | CHAR(1)                        | Yes      |                      |                                |
|  10 | 受入日                         | RCVDT                          | DATE                           | Yes      |                      |                                |
|  11 | 受入担当者コード               | RCVTANCD                       | VARCHAR2(8)                    | Yes      |                      |                                |
|  12 | 検査日                         | TSTDT                          | DATE                           |          |                      |                                |
|  13 | 検査担当者コード               | TSTTANCD                       | VARCHAR2(8)                    |          |                      |                                |
|  14 | 検収日                         | CHKDT                          | DATE                           |          |                      |                                |
|  15 | 検収担当者コード               | CHKTANCD                       | VARCHAR2(8)                    |          |                      |                                |
|  16 | 受入数                         | RCVQTY                         | NUMBER(10, 2)                  | Yes      |                      |                                |
|  17 | 受入単位コード                 | RCVUNIT                        | VARCHAR2(3)                    | Yes      |                      |                                |
|  18 | 入数                           | INQTY                          | NUMBER(10, 2)                  | Yes      |                      |                                |
|  19 | 良品数                         | OKQTY                          | NUMBER(10, 2)                  | Yes      |                      |                                |
|  20 | 不良数                         | NGQTY                          | NUMBER(10, 2)                  | Yes      |                      |                                |
|  21 | 不良理由コード                 | NGRSNCD                        | VARCHAR2(2)                    |          |                      |                                |
|  22 | 検収量                         | QTY                            | NUMBER(10, 2)                  | Yes      |                      |                                |
|  23 | 単位コード                     | UNIT                           | VARCHAR2(3)                    | Yes      |                      |                                |
|  24 | 品目重量                       | WEIGHT                         | NUMBER(7, 3)                   | Yes      |                      |                                |
|  25 | 品目総重量                     | TWEIGHT                        | NUMBER(9, 3)                   | Yes      |                      |                                |
|  26 | 仮単価区分                     | KPKBN                          | CHAR(1)                        | Yes      |                      |                                |
|  27 | 単価区分                       | PKBN                           | CHAR(1)                        | Yes      |                      |                                |
|  28 | 単価                           | PRICE                          | NUMBER(11, 2)                  | Yes      |                      |                                |
|  29 | 金額                           | AMOUNT                         | NUMBER(10, 0)                  | Yes      |                      |                                |
|  30 | 消費税区分                     | TAXKBN                         | CHAR(1)                        | Yes      |                      |                                |
|  31 | 消費税                         | TAX                            | NUMBER(9, 0)                   | Yes      |                      |                                |
|  32 | 製造事業部コード               | SEIBUCD                        | VARCHAR2(3)                    | Yes      |                      |                                |
|  33 | 勘定科目コード                 | SBCD                           | VARCHAR2(10)                   | Yes      |                      |                                |
|  34 | 原価科目コード                 | CSBCD                          | VARCHAR2(10)                   | Yes      |                      |                                |
|  35 | 在庫ロット番号                 | ZILOTNO                        | VARCHAR2(15)                   |          |                      |                                |
|  36 | 備考                           | NOTE                           | VARCHAR2(60)                   |          |                      |                                |
|  37 | 税抜金額                       | NOTAXAMT                       | NUMBER(10, 0)                  | Yes      |                      |                                |
|  38 | 消費税率                       | TAXRATE                        | NUMBER(3, 0)                   | Yes      |                      |                                |
|  39 | 軽減税率対象フラグ             | KGZEIFLG                       | CHAR(1)                        | Yes      |                      |                                |
|  40 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  41 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  42 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  43 |                                | UPDTDT                         | DATE                           |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_D3360                       | RCVNO,LINENO                             | Yes        |                                |
|   2 | IDX_D3360_PO                   | PONO,POLINENO                            |            |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_D3360                       | PRIMARY KEY                    | RCVNO,LINENO                   |
|   2 | SYS_C00100159                  | CHECK                          | "RCVNO" IS NOT NULL            |
|   3 | SYS_C00100160                  | CHECK                          | "LINENO" IS NOT NULL           |
|   4 | SYS_C00100161                  | CHECK                          | "TRKBN" IS NOT NULL            |
|   5 | SYS_C00100162                  | CHECK                          | "PONO" IS NOT NULL             |
|   6 | SYS_C00100163                  | CHECK                          | "POLINENO" IS NOT NULL         |
|   7 | SYS_C00100164                  | CHECK                          | "STATUS" IS NOT NULL           |
|   8 | SYS_C00100165                  | CHECK                          | "RCVTSTKBN" IS NOT NULL        |
|   9 | SYS_C00100166                  | CHECK                          | "RCVCHKKBN" IS NOT NULL        |
|  10 | SYS_C00100167                  | CHECK                          | "EDKBN" IS NOT NULL            |
|  11 | SYS_C00100168                  | CHECK                          | "RCVDT" IS NOT NULL            |
|  12 | SYS_C00100169                  | CHECK                          | "RCVTANCD" IS NOT NULL         |
|  13 | SYS_C00100170                  | CHECK                          | "RCVQTY" IS NOT NULL           |
|  14 | SYS_C00100171                  | CHECK                          | "RCVUNIT" IS NOT NULL          |
|  15 | SYS_C00100172                  | CHECK                          | "INQTY" IS NOT NULL            |
|  16 | SYS_C00100173                  | CHECK                          | "OKQTY" IS NOT NULL            |
|  17 | SYS_C00100174                  | CHECK                          | "NGQTY" IS NOT NULL            |
|  18 | SYS_C00100175                  | CHECK                          | "QTY" IS NOT NULL              |
|  19 | SYS_C00100176                  | CHECK                          | "UNIT" IS NOT NULL             |
|  20 | SYS_C00100177                  | CHECK                          | "WEIGHT" IS NOT NULL           |
|  21 | SYS_C00100178                  | CHECK                          | "TWEIGHT" IS NOT NULL          |
|  22 | SYS_C00100179                  | CHECK                          | "KPKBN" IS NOT NULL            |
|  23 | SYS_C00100180                  | CHECK                          | "PKBN" IS NOT NULL             |
|  24 | SYS_C00100181                  | CHECK                          | "PRICE" IS NOT NULL            |
|  25 | SYS_C00100182                  | CHECK                          | "AMOUNT" IS NOT NULL           |
|  26 | SYS_C00100183                  | CHECK                          | "TAXKBN" IS NOT NULL           |
|  27 | SYS_C00100184                  | CHECK                          | "TAX" IS NOT NULL              |
|  28 | SYS_C00100185                  | CHECK                          | "SEIBUCD" IS NOT NULL          |
|  29 | SYS_C00100186                  | CHECK                          | "SBCD" IS NOT NULL             |
|  30 | SYS_C00100187                  | CHECK                          | "CSBCD" IS NOT NULL            |
|  31 | SYS_C00100188                  | CHECK                          | "NOTAXAMT" IS NOT NULL         |
|  32 | SYS_C00100189                  | CHECK                          | "TAXRATE" IS NOT NULL          |
|  33 | SYS_C00100190                  | CHECK                          | "KGZEIFLG" IS NOT NULL         |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_D3360_M0080                 | CSBCD                                    | PFW.M0080                      | CSBCD                                    |              |              |
|   2 | FK_D3360_M0090                 | SBCD                                     | PFW.M0090                      | SBCD                                     |              |              |
|   3 | FK_D3360_M0160                 | NGRSNCD                                  | PFW.M0160                      | RSNCD                                    |              |              |
|   4 | FK_D3360_M0510                 | SEIBUCD                                  | PFW.M0510                      | BUCD                                     |              |              |
|   5 | FK_D3360_M0540_CHK             | CHKTANCD                                 | PFW.M0540                      | TANCD                                    |              |              |
|   6 | FK_D3360_M0540_RCV             | RCVTANCD                                 | PFW.M0540                      | TANCD                                    |              |              |
|   7 | FK_D3360_M0540_TST             | TSTTANCD                                 | PFW.M0540                      | TANCD                                    |              |              |
|   8 | FK_D3360_S0910_TH              | RCVUNIT                                  | PFW.S0910                      | UNIT                                     |              |              |
|   9 | FK_D3360_S0910_ZI              | UNIT                                     | PFW.S0910                      | UNIT                                     |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_D3360                      | Insert,Update                            | Before row           |                                |
|   2 | TRG_D3360_UPDPRICE             | Insert,Update                            | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW                                                                                                  |
|   2 | TABLE_NAME                     | D3360                                                                                                |
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
|  20 | NUM_ROWS                       | 0                                                                                                    |
|  21 | BLOCKS                         | 0                                                                                                    |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 0                                                                                                    |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 0                                                                                                    |
|  33 | LAST_ANALYZED                  | 2025/11/08 7:00:14                                                                                   |
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


