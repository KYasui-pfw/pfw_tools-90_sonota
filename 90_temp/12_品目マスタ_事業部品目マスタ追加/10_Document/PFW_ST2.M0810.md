# 品目マスタ (M0810)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     | rBOM                                                                                                 |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | PFW_ST2                                                                                              |
| 物理テーブル名                 | M0810                                                                                                |
| 論理テーブル名                 | 品目マスタ                                                                                           |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/10/10                                                                                           |
| RDBMS                          | Oracle Database 19c Standard Edition 2 Release 19.0.0.0.0 - Production 19.0.0.0.0                    |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 品目コード                     | HMCD                           | VARCHAR2(30)                   | Yes (PK) |                      |                                |
|   2 | 品名                           | HMNM                           | VARCHAR2(40)                   |          |                      |                                |
|   3 | 品名(全角)                     | HMWNM                          | VARCHAR2(80)                   |          |                      |                                |
|   4 | 型式                           | MODEL                          | VARCHAR2(80)                   |          |                      |                                |
|   5 | 型式(全角)                     | MODELW                         | VARCHAR2(160)                  |          |                      |                                |
|   6 | メーカー                       | MAKER                          | VARCHAR2(100)                  |          |                      |                                |
|   7 | 材質                           | MATERIAL                       | VARCHAR2(100)                  |          |                      |                                |
|   8 | 処理名                         | PROCESS                        | VARCHAR2(100)                  |          |                      |                                |
|   9 | 品目区分                       | HMKBN                          | CHAR(1)                        |          |                      |                                |
|  10 | 品目群コード                   | HMGUNCD                        | VARCHAR2(3)                    |          |                      |                                |
|  11 | 品目分類コード                 | HMBUNCD                        | VARCHAR2(3)                    |          |                      |                                |
|  12 | 標準製造事業部コード           | BUCD                           | VARCHAR2(3)                    |          |                      |                                |
|  13 | 原価科目コード                 | CSBCD                          | VARCHAR2(10)                   |          |                      |                                |
|  14 | 在庫単位コード                 | ZUNITCD                        | VARCHAR2(3)                    |          |                      |                                |
|  15 | 品目重量                       | WEIGHT                         | NUMBER(7, 3)                   |          |                      |                                |
|  16 | 発注単位コード                 | HUNITCD                        | VARCHAR2(3)                    |          |                      |                                |
|  17 | 入数                           | HIRIQTY                        | NUMBER(12, 2)                  |          |                      |                                |
|  18 | 単価区分                       | PKBN                           | CHAR(1)                        |          |                      |                                |
|  19 | 受入検査区分                   | RCVTSTKBN                      | CHAR(1)                        |          |                      |                                |
|  20 | 受入検収区分                   | RCVCHKKBN                      | CHAR(1)                        |          |                      |                                |
|  21 | 調達リードタイム               | SUPLT                          | NUMBER(3, 0)                   |          |                      |                                |
|  22 | 標準消費税区分                 | TAXKBN                         | CHAR(1)                        |          |                      |                                |
|  23 | 標準原単価                     | COST                           | NUMBER(11, 2)                  |          |                      |                                |
|  24 | 標準売単価                     | PRICE                          | NUMBER(11, 2)                  |          |                      |                                |
|  25 | 形状                           | SHAPEKBN                       | CHAR(1)                        |          |                      |                                |
|  26 | サイズ_X                       | SIZEX                          | NUMBER(9, 3)                   |          |                      |                                |
|  27 | サイズ_Y                       | SIZEY                          | NUMBER(9, 3)                   |          |                      |                                |
|  28 | サイズ_Z                       | SIZEZ                          | NUMBER(9, 3)                   |          |                      |                                |
|  29 | 形状量                         | SHAPEQTY                       | NUMBER(10, 3)                  |          |                      |                                |
|  30 | 形状単位コード                 | SHAPEUNIT                      | VARCHAR2(3)                    |          |                      |                                |
|  31 | 工程自動展開区分               | KTEXPKBN                       | CHAR(1)                        |          |                      |                                |
|  32 | 自動展開区分                   | ATEXPKBN                       | CHAR(1)                        |          |                      |                                |
|  33 | 展開停止区分                   | EXPSTPKBN                      | CHAR(1)                        |          |                      |                                |
|  34 | 製番区分コード                 | SEIKBN                         | VARCHAR2(2)                    |          |                      |                                |
|  35 | 生産中止日付                   | STOPDT                         | DATE                           |          |                      |                                |
|  36 | 生産中止備考                   | STOPNOTE                       | VARCHAR2(20)                   |          |                      |                                |
|  37 | 備考                           | NOTE                           | VARCHAR2(100)                  |          |                      |                                |
|  38 | 有効状態                       | VALFLG                         | CHAR(1)                        |          |                      |                                |
|  39 |                                | INSTID                         | VARCHAR2(8)                    |          |                      |                                |
|  40 |                                | INSTDT                         | DATE                           |          |                      |                                |
|  41 |                                | UPDTID                         | VARCHAR2(8)                    |          |                      |                                |
|  42 |                                | UPDTDT                         | DATE                           |          |                      |                                |
|  43 | ミスミ品区分                   | MISUMIHNKBN                    | CHAR(1)                        | Yes      |                      |                                |
|  44 | 基準原価係数適用               | STDGNKKSKBN                    | CHAR(1)                        | Yes      | '1'                  |                                |
|  45 | 国内売単価係数適用             | KKNAIBTNKKBN                   | CHAR(1)                        | Yes      | '1'                  |                                |
|  46 | 工程展開用区分                 | KTTNKIKBN                      | CHAR(1)                        | Yes      | '2'                  |                                |
|  47 | 出庫区分                       | SYUKOKBN                       | CHAR(1)                        | Yes      | '1'                  |                                |
|  48 | コンバージョン時同梱区分       | CVDOKONKBN                     | CHAR(1)                        | Yes      | '2'                  |                                |
|  49 | セクション                     | SECTION                        | VARCHAR2(2)                    |          |                      |                                |
|  50 | クラス名                       | CLASSNM                        | VARCHAR2(255)                  | Yes      | ' '                  |                                |
|  51 | 設計分類                       | EGROUP                         | VARCHAR2(255)                  |          |                      |                                |
|  52 | CAT                            | CAT                            | VARCHAR2(200)                  |          |                      |                                |
|  53 | 熱処理                         | HEATTRTMT                      | VARCHAR2(255)                  |          |                      |                                |
|  54 | 表面処理                       | SURFTRTTMT                     | VARCHAR2(255)                  |          |                      |                                |
|  55 | 日程コード                     | NTCD                           | VARCHAR2(6)                    |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | PK_M0810                       | HMCD                                     | Yes        |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | PK_M0810                       | PRIMARY KEY                    | HMCD                           |
|   2 | SYS_C0063832                   | CHECK                          | "HMCD" IS NOT NULL             |
|   3 | SYS_C0063833                   | CHECK                          | "HMNM" IS NOT NULL             |
|   4 | SYS_C0063834                   | CHECK                          | "HMWNM" IS NOT NULL            |
|   5 | SYS_C0063835                   | CHECK                          | "HMKBN" IS NOT NULL            |
|   6 | SYS_C0063836                   | CHECK                          | "HMGUNCD" IS NOT NULL          |
|   7 | SYS_C0063837                   | CHECK                          | "HMBUNCD" IS NOT NULL          |
|   8 | SYS_C0063838                   | CHECK                          | "ZUNITCD" IS NOT NULL          |
|   9 | SYS_C0063839                   | CHECK                          | "WEIGHT" IS NOT NULL           |
|  10 | SYS_C0063840                   | CHECK                          | "HUNITCD" IS NOT NULL          |
|  11 | SYS_C0063841                   | CHECK                          | "HIRIQTY" IS NOT NULL          |
|  12 | SYS_C0063842                   | CHECK                          | "PKBN" IS NOT NULL             |
|  13 | SYS_C0063843                   | CHECK                          | "RCVTSTKBN" IS NOT NULL        |
|  14 | SYS_C0063844                   | CHECK                          | "RCVCHKKBN" IS NOT NULL        |
|  15 | SYS_C0063845                   | CHECK                          | "SUPLT" IS NOT NULL            |
|  16 | SYS_C0063846                   | CHECK                          | "TAXKBN" IS NOT NULL           |
|  17 | SYS_C0063847                   | CHECK                          | "COST" IS NOT NULL             |
|  18 | SYS_C0063848                   | CHECK                          | "SHAPEKBN" IS NOT NULL         |
|  19 | SYS_C0063849                   | CHECK                          | "SHAPEQTY" IS NOT NULL         |
|  20 | SYS_C0063850                   | CHECK                          | "SHAPEUNIT" IS NOT NULL        |
|  21 | SYS_C0063851                   | CHECK                          | "KTEXPKBN" IS NOT NULL         |
|  22 | SYS_C0063852                   | CHECK                          | "ATEXPKBN" IS NOT NULL         |
|  23 | SYS_C0063853                   | CHECK                          | "EXPSTPKBN" IS NOT NULL        |
|  24 | SYS_C0063854                   | CHECK                          | "VALFLG" IS NOT NULL           |
|  25 | SYS_C0063855                   | CHECK                          | "MISUMIHNKBN" IS NOT NULL      |
|  26 | SYS_C0063856                   | CHECK                          | "STDGNKKSKBN" IS NOT NULL      |
|  27 | SYS_C0063857                   | CHECK                          | "KKNAIBTNKKBN" IS NOT NULL     |
|  28 | SYS_C0063858                   | CHECK                          | "KTTNKIKBN" IS NOT NULL        |
|  29 | SYS_C0063859                   | CHECK                          | "SYUKOKBN" IS NOT NULL         |
|  30 | SYS_C0063860                   | CHECK                          | "CVDOKONKBN" IS NOT NULL       |
|  31 | SYS_C0063861                   | CHECK                          | "CLASSNM" IS NOT NULL          |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_M0810_M0060                 | HMGUNCD                                  | PFW_ST2.M0060                  | HMGUNCD                                  |              |              |
|   2 | FK_M0810_M0070                 | HMBUNCD                                  | PFW_ST2.M0070                  | HMBUNCD                                  |              |              |
|   3 | FK_M0810_M0080                 | CSBCD                                    | PFW_ST2.M0080                  | CSBCD                                    |              |              |
|   4 | FK_M0810_M0170                 | SEIKBN                                   | PFW_ST2.M0170                  | SEIKBN                                   |              |              |
|   5 | FK_M0810_M0190                 | NTCD                                     | PFW_ST2.M0190                  | NTCD                                     |              |              |
|   6 | FK_M0810_M0510                 | BUCD                                     | PFW_ST2.M0510                  | BUCD                                     |              |              |
|   7 | FK_M0810_S0910_H               | HUNITCD                                  | PFW_ST2.S0910                  | UNIT                                     |              |              |
|   8 | FK_M0810_S0910_SP              | SHAPEUNIT                                | PFW_ST2.S0910                  | UNIT                                     |              |              |
|   9 | FK_M0810_S0910_Z               | ZUNITCD                                  | PFW_ST2.S0910                  | UNIT                                     |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | FK_D0010_M0810                 | HMCD                                     | PFW_ST2.D0010                  | HMCD                                     |              |              |
|   2 | FK_D0120_M0810                 | HMCD                                     | PFW_ST2.D0120                  | HMCD                                     |              |              |
|   3 | FK_D0220_M0810                 | HMCD                                     | PFW_ST2.D0220                  | HMCD                                     |              |              |
|   4 | FK_D0320_M0810                 | HMCD                                     | PFW_ST2.D0320                  | HMCD                                     |              |              |
|   5 | FK_D0350_M0810                 | HMCD                                     | PFW_ST2.D0350                  | HMCD                                     |              |              |
|   6 | FK_D0420_M0810                 | HMCD                                     | PFW_ST2.D0420                  | HMCD                                     |              |              |
|   7 | FK_D0430_M0810                 | HMCD                                     | PFW_ST2.D0430                  | HMCD                                     |              |              |
|   8 | FK_D0720_M0810                 | HMCD                                     | PFW_ST2.D0720                  | HMCD                                     |              |              |
|   9 | FK_D1020_M0810                 | HMCD                                     | PFW_ST2.D1020                  | HMCD                                     |              |              |
|  10 | FK_D3010_M0810                 | HMCD                                     | PFW_ST2.D3010                  | HMCD                                     |              |              |
|  11 | FK_D3110_M0810                 | HMCD                                     | PFW_ST2.D3110                  | HMCD                                     |              |              |
|  12 | FK_D3130_M0810                 | HMCD                                     | PFW_ST2.D3130                  | HMCD                                     |              |              |
|  13 | FK_D3220_M0810                 | HMCD                                     | PFW_ST2.D3220                  | HMCD                                     |              |              |
|  14 | FK_D3320_M0810                 | HMCD                                     | PFW_ST2.D3320                  | HMCD                                     |              |              |
|  15 | FK_D3340_M0810                 | HMCD                                     | PFW_ST2.D3340                  | HMCD                                     |              |              |
|  16 | FK_D3420_M0810                 | HMCD                                     | PFW_ST2.D3420                  | HMCD                                     |              |              |
|  17 | FK_D3550_M0810                 | HMCD                                     | PFW_ST2.D3550                  | HMCD                                     |              |              |
|  18 | FK_D3570_M0810                 | HMCD                                     | PFW_ST2.D3570                  | HMCD                                     |              |              |
|  19 | FK_D3590_M0810                 | HMCD                                     | PFW_ST2.D3590                  | HMCD                                     |              |              |
|  20 | FK_D3620_M0810                 | HMCD                                     | PFW_ST2.D3620                  | HMCD                                     |              |              |
|  21 | FK_D3720_M0810                 | HMCD                                     | PFW_ST2.D3720                  | HMCD                                     |              |              |
|  22 | FK_D3730_M0810                 | HMCD                                     | PFW_ST2.D3730                  | HMCD                                     |              |              |
|  23 | FK_D3740_M0810                 | HMCD                                     | PFW_ST2.D3740                  | HMCD                                     |              |              |
|  24 | FK_D3740_M0810_OYA             | HMCD                                     | PFW_ST2.D3740                  | OYAHMCD                                  |              |              |
|  25 | FK_D3810_M0810                 | HMCD                                     | PFW_ST2.D3810                  | HMCD                                     |              |              |
|  26 | FK_D3820_M0810                 | HMCD                                     | PFW_ST2.D3820                  | HMCD                                     |              |              |
|  27 | FK_D4010_M0810                 | HMCD                                     | PFW_ST2.D4010                  | HMCD                                     |              |              |
|  28 | FK_D4020_M0810                 | HMCD                                     | PFW_ST2.D4020                  | HMCD                                     |              |              |
|  29 | FK_D4230_M0810                 | HMCD                                     | PFW_ST2.D4230                  | HMCD                                     |              |              |
|  30 | FK_D4310_M0810                 | HMCD                                     | PFW_ST2.D4310                  | HMCD                                     |              |              |
|  31 | FK_D4320_M0810                 | HMCD                                     | PFW_ST2.D4320                  | HMCD                                     |              |              |
|  32 | FK_D7010_M0810                 | HMCD                                     | PFW_ST2.D7010                  | HMCD                                     |              |              |
|  33 | FK_D7040_M0810                 | HMCD                                     | PFW_ST2.D7040                  | HMCD                                     |              |              |
|  34 | FK_D7110_M0810                 | HMCD                                     | PFW_ST2.D7110                  | HMCD                                     |              |              |
|  35 | FK_DK050_M0810                 | HMCD                                     | PFW_ST2.DK050                  | HMCD                                     |              |              |
|  36 | FK_DK130_M0810                 | HMCD                                     | PFW_ST2.DK130                  | HMCD                                     |              |              |
|  37 | FK_M0820_M0810                 | HMCD                                     | PFW_ST2.M0820                  | HMCD                                     |              |              |
|  38 | FK_M0840_M0810                 | HMCD                                     | PFW_ST2.M0840                  | HMCD                                     |              |              |
|  39 | FK_M0850_M0810_KO              | HMCD                                     | PFW_ST2.M0850                  | KOHMCD                                   |              |              |
|  40 | FK_M0850_M0810_OYA             | HMCD                                     | PFW_ST2.M0850                  | OYAHMCD                                  |              |              |
|  41 | FK_M0860_M0810                 | HMCD                                     | PFW_ST2.M0860                  | HMCD                                     |              |              |
|  42 | FK_M0910_M0810                 | HMCD                                     | PFW_ST2.M0910                  | HMCD                                     | CASCADE      |              |
|  43 | FK_M0920_M0810                 | HMCD                                     | PFW_ST2.M0920                  | HMCD                                     | CASCADE      |              |
|  44 | FK_M0930_M0810                 | HMCD                                     | PFW_ST2.M0930                  | HMCD                                     | CASCADE      |              |
|  45 | FK_M3520_M0810                 | HMCD                                     | PFW_ST2.D3520                  | HMCD                                     |              |              |
|  46 | FK_MK020_M0810                 | HMCD                                     | PFW_ST2.MK020                  | OYAHMCD                                  | CASCADE      |              |
|  47 | FK_MK070_M0810                 | HMCD                                     | PFW_ST2.MK070                  | HMCD                                     | CASCADE      |              |



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_M0810                      | Insert,Update                            | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | PFW_ST2                                                                                              |
|   2 | TABLE_NAME                     | M0810                                                                                                |
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
|  20 | NUM_ROWS                       | 187940                                                                                               |
|  21 | BLOCKS                         | 5620                                                                                                 |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 201                                                                                                  |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 187940                                                                                               |
|  33 | LAST_ANALYZED                  | 2025/09/26 7:00:11                                                                                   |
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


