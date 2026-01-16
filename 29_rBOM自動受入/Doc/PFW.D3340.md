# 発注明細ファイル (D3340)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW                                                                                                  |
| 物理テーブル名                 | D3340                                                                                                |
| 論理テーブル名                 | 発注明細ファイル                                                                                     |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/12/15                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 発注番号                       | PONO                           | VARCHAR2(15)                   | Yes (PK) |                      |                                |
|   2 | 行番号                         | LINENO                         | NUMBER(3, 0)                   | Yes (PK) |                      |                                |
|   3 | 取引区分                       | TRKBN                          | CHAR(1)                        | Yes      |                      |                                |
|   4 | 表示順                         | SRTNO                          | NUMBER(6, 0)                   | Yes      |                      |                                |
|   5 | 受注番号                       | JUNO                           | VARCHAR2(15)                   |          |                      |                                |
|   6 | 受注行番号                     | JULINENO                       | NUMBER(3, 0)                   |          |                      |                                |
|   7 | 製番                           | SEINO                          | VARCHAR2(15)                   |          |                      |                                |
|   8 | リスト番号                     | LISTNO                         | VARCHAR2(60)                   |          |                      |                                |
|   9 | 発生訂番                       | VERNO                          | NUMBER(4, 0)                   |          |                      |                                |
|  10 | 状態                           | STATUS                         | CHAR(1)                        | Yes      |                      |                                |
|  11 | 受入検査区分                   | RCVTSTKBN                      | CHAR(1)                        | Yes      |                      |                                |
|  12 | 受入検収区分                   | RCVCHKKBN                      | CHAR(1)                        | Yes      |                      |                                |
|  13 | 理由コード                     | RSNCD                          | VARCHAR2(2)                    |          |                      |                                |
|  14 | 品目変更区分                   | HMCNGKBN                       | CHAR(1)                        | Yes      |                      |                                |
|  15 | 部品種類                       | PARTSKBN                       | CHAR(1)                        | Yes      |                      |                                |
|  16 | 品目コード                     | HMCD                           | VARCHAR2(30)                   |          |                      |                                |
|  17 | 品名                           | HMNM                           | VARCHAR2(40)                   | Yes      |                      |                                |
|  18 | 品名(全角)                     | HMWNM                          | VARCHAR2(80)                   | Yes      |                      |                                |
|  19 | 型式                           | MODEL                          | VARCHAR2(80)                   |          |                      |                                |
|  20 | 型式(全角)                     | MODELW                         | VARCHAR2(160)                  |          |                      |                                |
|  21 | メーカー                       | MAKER                          | VARCHAR2(30)                   |          |                      |                                |
|  22 | 材質                           | MATERIAL                       | VARCHAR2(20)                   |          |                      |                                |
|  23 | 処理名                         | PROCESS                        | VARCHAR2(100)                  |          |                      |                                |
|  24 | 形状                           | SHAPEKBN                       | CHAR(1)                        | Yes      |                      |                                |
|  25 | サイズ_X                       | SIZEX                          | NUMBER(9, 3)                   |          |                      |                                |
|  26 | サイズ_Y                       | SIZEY                          | NUMBER(9, 3)                   |          |                      |                                |
|  27 | サイズ_Z                       | SIZEZ                          | NUMBER(9, 3)                   |          |                      |                                |
|  28 | 形状数                         | SHAPEQTY                       | NUMBER(10, 3)                  | Yes      |                      |                                |
|  29 | 工程コード                     | KTCD                           | VARCHAR2(5)                    |          |                      |                                |
|  30 | 希望納期                       | DRVDT                          | DATE                           | Yes      |                      |                                |
|  31 | 回答納期                       | RECDT                          | DATE                           |          |                      |                                |
|  32 | 発注数                         | THQTY                          | NUMBER(10, 2)                  | Yes      |                      |                                |
|  33 | 発注単位コード                 | THUNIT                         | VARCHAR2(3)                    | Yes      |                      |                                |
|  34 | 入数                           | INQTY                          | NUMBER(10, 2)                  | Yes      |                      |                                |
|  35 | 発注量                         | QTY                            | NUMBER(10, 2)                  | Yes      |                      |                                |
|  36 | 単位コード                     | UNIT                           | VARCHAR2(3)                    | Yes      |                      |                                |
|  37 | 品目重量                       | WEIGHT                         | NUMBER(7, 3)                   | Yes      |                      |                                |
|  38 | 品目総重量                     | TWEIGHT                        | NUMBER(9, 3)                   | Yes      |                      |                                |
|  39 | 仮単価区分                     | KPKBN                          | CHAR(1)                        | Yes      |                      |                                |
|  40 | 仮単価理由コード               | KPRSNCD                        | VARCHAR2(2)                    |          |                      |                                |
|  41 | 単価決定予定日                 | PCMMTDT                        | DATE                           |          |                      |                                |
|  42 | 単価区分                       | PKBN                           | CHAR(1)                        | Yes      |                      |                                |
|  43 | 単価                           | PRICE                          | NUMBER(11, 2)                  | Yes      |                      |                                |
|  44 | 金額                           | AMOUNT                         | NUMBER(10, 0)                  | Yes      |                      |                                |
|  45 | 消費税区分                     | TAXKBN                         | CHAR(1)                        | Yes      |                      |                                |
|  46 | 消費税                         | TAX                            | NUMBER(9, 0)                   | Yes      |                      |                                |
|  47 | 注文書発行区分                 | PRNKBN                         | CHAR(1)                        | Yes      |                      |                                |
|  48 | 注文書発行日                   | PRNDT                          | DATE                           |          |                      |                                |
|  49 | 入荷フラグ                     | NKFLG                          | NUMBER(1, 0)                   |          |                      |                                |
|  50 | 納入区分                       | NNKBN                          | CHAR(1)                        | Yes      |                      |                                |
|  51 | 納入先コード                   | NNCD                           | VARCHAR2(10)                   |          |                      |                                |
|  52 | 納入場所                       | NNBASHO                        | VARCHAR2(30)                   |          |                      |                                |
|  53 | 製造事業部コード               | SEIBUCD                        | VARCHAR2(3)                    | Yes      |                      |                                |
|  54 | 勘定科目コード                 | SBCD                           | VARCHAR2(10)                   | Yes      |                      |                                |
|  55 | 原価科目コード                 | CSBCD                          | VARCHAR2(10)                   | Yes      |                      |                                |
|  56 | 発注指示番号                   | PRNO                           | VARCHAR2(15)                   |          |                      |                                |
|  57 | 発注指示行番号                 | PRLINENO                       | NUMBER(3, 0)                   |          |                      |                                |
|  58 | 備考                           | NOTE                           | VARCHAR2(60)                   |          |                      |                                |
|  59 | POST回答日時                   | POSTRECDTM                     | DATE                           |          |                      |                                |
|  60 | POST回答担当者                 | POSTRECTAN                     | VARCHAR2(20)                   |          |                      |                                |
|  61 | POST回答備考                   | POSTRECNOTE                    | VARCHAR2(60)                   |          |                      |                                |
|  62 | 税抜金額                       | NOTAXAMT                       | NUMBER(10, 0)                  | Yes      |                      |                                |
|  63 | 消費税率                       | TAXRATE                        | NUMBER(3, 0)                   | Yes      |                      |                                |
|  64 | 軽減税率対象フラグ             | KGZEIFLG                       | CHAR(1)                        | Yes      |                      |                                |
|  65 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  66 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  67 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  68 |                                | UPDTDT                         | DATE                           |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_D3340                       | PONO,LINENO                              | Yes        |                                |
|   2 | IDX_D3340_HMCD                 | HMCD                                     |            |                                |
|   3 | IDX_D3340_HMCD_TRKBN           | HMCD,TRKBN,STATUS                        |            |                                |
|   4 | IDX_D3340_HMNM_MODEL           | HMNM,MODEL                               |            |                                |
|   5 | IDX_D3340_JUNO_JULINENO        | JUNO,JULINENO                            |            |                                |
|   6 | IDX_D3340_LISTNO               | SEINO,LISTNO                             |            |                                |
|   7 | IDX_D3340_MODEL                | MODEL                                    |            |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_D3340                       | PRIMARY KEY                    | PONO,LINENO                    |
|   2 | SYS_C0098554                   | CHECK                          | "PONO" IS NOT NULL             |
|   3 | SYS_C0098555                   | CHECK                          | "LINENO" IS NOT NULL           |
|   4 | SYS_C0098556                   | CHECK                          | "TRKBN" IS NOT NULL            |
|   5 | SYS_C0098557                   | CHECK                          | "SRTNO" IS NOT NULL            |
|   6 | SYS_C0098558                   | CHECK                          | "STATUS" IS NOT NULL           |
|   7 | SYS_C0098559                   | CHECK                          | "RCVTSTKBN" IS NOT NULL        |
|   8 | SYS_C0098560                   | CHECK                          | "RCVCHKKBN" IS NOT NULL        |
|   9 | SYS_C0098561                   | CHECK                          | "HMCNGKBN" IS NOT NULL         |
|  10 | SYS_C0098562                   | CHECK                          | "PARTSKBN" IS NOT NULL         |
|  11 | SYS_C0098563                   | CHECK                          | "HMNM" IS NOT NULL             |
|  12 | SYS_C0098564                   | CHECK                          | "HMWNM" IS NOT NULL            |
|  13 | SYS_C0098565                   | CHECK                          | "SHAPEKBN" IS NOT NULL         |
|  14 | SYS_C0098566                   | CHECK                          | "SHAPEQTY" IS NOT NULL         |
|  15 | SYS_C0098567                   | CHECK                          | "DRVDT" IS NOT NULL            |
|  16 | SYS_C0098568                   | CHECK                          | "THQTY" IS NOT NULL            |
|  17 | SYS_C0098569                   | CHECK                          | "THUNIT" IS NOT NULL           |
|  18 | SYS_C0098570                   | CHECK                          | "INQTY" IS NOT NULL            |
|  19 | SYS_C0098571                   | CHECK                          | "QTY" IS NOT NULL              |
|  20 | SYS_C0098572                   | CHECK                          | "UNIT" IS NOT NULL             |
|  21 | SYS_C0098573                   | CHECK                          | "WEIGHT" IS NOT NULL           |
|  22 | SYS_C0098574                   | CHECK                          | "TWEIGHT" IS NOT NULL          |
|  23 | SYS_C0098575                   | CHECK                          | "KPKBN" IS NOT NULL            |
|  24 | SYS_C0098576                   | CHECK                          | "PKBN" IS NOT NULL             |
|  25 | SYS_C0098577                   | CHECK                          | "PRICE" IS NOT NULL            |
|  26 | SYS_C0098578                   | CHECK                          | "AMOUNT" IS NOT NULL           |
|  27 | SYS_C0098579                   | CHECK                          | "TAXKBN" IS NOT NULL           |
|  28 | SYS_C0098580                   | CHECK                          | "TAX" IS NOT NULL              |
|  29 | SYS_C0098581                   | CHECK                          | "PRNKBN" IS NOT NULL           |
|  30 | SYS_C0098582                   | CHECK                          | "NNKBN" IS NOT NULL            |
|  31 | SYS_C0098583                   | CHECK                          | "SEIBUCD" IS NOT NULL          |
|  32 | SYS_C0098584                   | CHECK                          | "SBCD" IS NOT NULL             |
|  33 | SYS_C0098585                   | CHECK                          | "CSBCD" IS NOT NULL            |
|  34 | SYS_C0098586                   | CHECK                          | "NOTAXAMT" IS NOT NULL         |
|  35 | SYS_C0098587                   | CHECK                          | "TAXRATE" IS NOT NULL          |
|  36 | SYS_C0098588                   | CHECK                          | "KGZEIFLG" IS NOT NULL         |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_D3340_M0080                 | CSBCD                                    | PFW.M0080                      | CSBCD                                    |              |              |
|   2 | FK_D3340_M0090                 | SBCD                                     | PFW.M0090                      | SBCD                                     |              |              |
|   3 | FK_D3340_M0160                 | RSNCD                                    | PFW.M0160                      | RSNCD                                    |              |              |
|   4 | FK_D3340_M0160_KP              | KPRSNCD                                  | PFW.M0160                      | RSNCD                                    |              |              |
|   5 | FK_D3340_M0410                 | KTCD                                     | PFW.M0410                      | KTCD                                     |              |              |
|   6 | FK_D3340_M0510_SEI             | SEIBUCD                                  | PFW.M0510                      | BUCD                                     |              |              |
|   7 | FK_D3340_M0810                 | HMCD                                     | PFW.M0810                      | HMCD                                     |              |              |
|   8 | FK_D3340_S910_TH               | THUNIT                                   | PFW.S0910                      | UNIT                                     |              |              |
|   9 | FK_D3340_S910_ZI               | UNIT                                     | PFW.S0910                      | UNIT                                     |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_D3370_D3340                 | PONO,LINENO                              | PFW.D3370                      | PONO,POLINENO                            |              |              |



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_D3340                      | Insert,Update                            | Before row           |                                |
|   2 | TRG_D3340_UPDT                 | Insert,Update,Delete                     | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW                                                                                                  |
|   2 | TABLE_NAME                     | D3340                                                                                                |
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
|  20 | NUM_ROWS                       | 10684                                                                                                |
|  21 | BLOCKS                         | 496                                                                                                  |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 246                                                                                                  |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 10684                                                                                                |
|  33 | LAST_ANALYZED                  | 2025/11/13 7:00:20                                                                                   |
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


