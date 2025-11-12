# 発注残 (T_RLSD_PUCH_ODR)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | EXPJ2                                                                                                |
| 物理テーブル名                 | T_RLSD_PUCH_ODR                                                                                      |
| 論理テーブル名                 | 発注残                                                                                               |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/07/29                                                                                           |
| RDBMS                          | Oracle Database 10g Release 10.2.0.1.0 - Production 10.2.0.1.0                                       |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 発注番号                       | PUCH_ODR_CD                    | VARCHAR2(100)                  | Yes (PK) |                      |                                |
|   2 | 品目番号                       | ITEM_CD                        | VARCHAR2(100)                  |          |                      |                                |
|   3 | 受入場所                       | WH_CD                          | VARCHAR2(100)                  |          |                      |                                |
|   4 | 備品発注品目名                 | NON_NO_ITEM_NAME               | VARCHAR2(160)                  |          |                      |                                |
|   5 | 備品発注製品区分               | NON_NO_ITEM_TYP                | NUMBER(2, 0)                   |          | 1                    |                                |
|   6 | 会社コード                     | COMPANY_CD                     | VARCHAR2(100)                  |          |                      |                                |
|   7 | 取引先コード                   | VEND_CD                        | VARCHAR2(100)                  |          |                      |                                |
|   8 | 工場コード                     | PLANT_CD                       | VARCHAR2(8)                    |          |                      |                                |
|   9 | 発注担当者                     | PUCH_ODR_PERSON                | VARCHAR2(160)                  |          |                      |                                |
|  10 | 発注着手日                     | PUCH_ODR_START_DATE            | DATE                           |          |                      |                                |
|  11 | 発注納期                       | PUCH_ODR_DLV_DATE              | DATE                           |          |                      |                                |
|  12 | 発注数                         | PUCH_ODR_QTY                   | NUMBER(18, 4)                  |          | 0                    |                                |
|  13 | 備品発注単位                   | NON_NO_ITEM_PUCH_ODR_UNIT      | VARCHAR2(48)                   |          |                      |                                |
|  14 | 単価区分                       | UNIT_COST_TYP                  | NUMBER(2, 0)                   |          | 1                    |                                |
|  15 | 単価                           | UNIT_COST                      | NUMBER(18, 4)                  |          | 0                    |                                |
|  16 | 加工費                         | PROCESSING_COST                | NUMBER(18, 4)                  |          | 0                    |                                |
|  17 | 材料費                         | MATERIAL_COST                  | NUMBER(18, 4)                  |          | 0                    |                                |
|  18 | その他経費                     | OTHER_OVERHEADS                | NUMBER(18, 4)                  |          | 0                    |                                |
|  19 | 値引金額                       | DISC_AMOUNT                    | NUMBER(18, 4)                  |          | 0                    |                                |
|  20 | 発注金額                       | PUCH_ODR_AMOUNT                | NUMBER(18, 4)                  |          | 0                    |                                |
|  21 | 発注発生処理区分               | PUCH_ODR_GNR_TYP               | NUMBER(2, 0)                   |          | 1                    |                                |
|  22 | 発注指示日                     | PUCH_ODR_INST_DATE             | DATE                           |          |                      |                                |
|  23 | 発注伝票発行済みフラグ         | PUCH_ODR_INST_SLIP_ISS_FLG     | NUMBER(1, 0)                   |          | 0                    |                                |
|  24 | 発注伝票発行日                 | PUCH_ODR_SLIP_ISS_DATE         | DATE                           |          | sysdate              |                                |
|  25 | 受入完了日                     | ACPT_CMPLT_DATE                | DATE                           |          |                      |                                |
|  26 | 発注状態区分                   | PUCH_ODR_STS_TYP               | NUMBER(2, 0)                   |          | 1                    |                                |
|  27 | 検査完了フラグ                 | INSPC_CMPLT_FLG                | NUMBER(1, 0)                   |          | 0                    |                                |
|  28 | 検査完了日                     | INSPC_CMPLT_DATE               | DATE                           |          |                      |                                |
|  29 | 回答納期                       | CONFIRM_DLV_DATE               | DATE                           |          |                      |                                |
|  30 | 回答納期備考                   | CONFIRM_DLV_DATE_COMMENT       | VARCHAR2(320)                  |          |                      |                                |
|  31 | 受給品区分                     | SPL_ITEM_TYP                   | NUMBER(2, 0)                   |          | 1                    |                                |
|  32 | 発注時受入検査区分             | ACPT_INSPC_TYP                 | NUMBER(2, 0)                   |          | 1                    |                                |
|  33 | 在庫管理フラグ                 | INV_CTRL_FLG                   | NUMBER(1, 0)                   |          | 0                    |                                |
|  34 | 作業計画番号                   | WORK_ODR_CD                    | VARCHAR2(100)                  |          |                      |                                |
|  35 | 仕掛作業コード                 | WORK_IN_PROC_CD                | VARCHAR2(100)                  |          |                      |                                |
|  36 | オーダデマンド番号             | OD_NO                          | VARCHAR2(100)                  |          |                      |                                |
|  37 | 発注備考                       | PUCH_ODR_COMMENT               | VARCHAR2(320)                  |          |                      |                                |
|  38 | 注文番号                       | ODR_CD                         | VARCHAR2(100)                  |          |                      |                                |
|  39 | 明細番号                       | DETAIL_NO                      | NUMBER(6, 0)                   |          | 0                    |                                |
|  40 | レート判定日                   | RATE_JUDGE_DATE                | DATE                           |          |                      |                                |
|  41 | 為替レート                     | EXCH_RATE                      | NUMBER(20, 6)                  |          | 0                    |                                |
|  42 | 税率1                          | TAX_RATE_1                     | NUMBER(18, 4)                  |          | 0                    |                                |
|  43 | 税率2                          | TAX_RATE_2                     | NUMBER(18, 4)                  |          | 0                    |                                |
|  44 | 税率3                          | TAX_RATE_3                     | NUMBER(18, 4)                  |          | 0                    |                                |
|  45 | 本体金額                       | NET_AMOUNT                     | NUMBER(18, 4)                  |          | 0                    |                                |
|  46 | 税額1                          | TAX_AMOUNT_1                   | NUMBER(18, 4)                  |          | 0                    |                                |
|  47 | 税額2                          | TAX_AMOUNT_2                   | NUMBER(18, 4)                  |          | 0                    |                                |
|  48 | 税額3                          | TAX_AMOUNT_3                   | NUMBER(18, 4)                  |          | 0                    |                                |
|  49 | 税込金額                       | AMOUNT_INCLUDE_TAX             | NUMBER(18, 4)                  |          | 0                    |                                |
|  50 | 邦貨金額                       | HOME_CUR_AMOUNT                | NUMBER(18, 4)                  |          | 0                    |                                |
|  51 | 消費税コード                   | TAX_CD                         | VARCHAR2(100)                  |          |                      |                                |
|  52 | 税端数区分                     | TAX_ROUND_TYP                  | NUMBER(2, 0)                   |          | 1                    |                                |
|  53 | 備品発注フラグ                 | NON_NO_ITEM_FLG                | NUMBER(1, 0)                   |          | 0                    |                                |
|  54 | ＥＤＩデータ出力済フラグ       | PUCH_ODR_EDI_ISS_FLG           | NUMBER(1, 0)                   |          | 0                    |                                |
|  55 | ＥＤＩデータ出力日             | PUCH_ODR_EDI_ISS_DATE          | DATE                           |          |                      |                                |
|  56 | ＥＤＩデータ取消出力日         | ODR_CANCEL_EDI_ISS_DATE        | DATE                           |          |                      |                                |
|  57 | ＦＡＸデータ出力済フラグ       | PUCH_ODR_FAX_ISS_FLG           | NUMBER(1, 0)                   |          | 0                    |                                |
|  58 | ＦＡＸデータ出力日             | PUCH_ODR_FAX_ISS_DATE          | DATE                           |          |                      |                                |
|  59 | ＭＡＩＬデータ出力済フラグ     | PUCH_ODR_MAIL_ISS_FLG          | NUMBER(1, 0)                   |          | 0                    |                                |
|  60 | ＭＡＩＬデータ出力日           | PUCH_ODR_MAIL_ISS_DATE         | DATE                           |          |                      |                                |
|  61 | 注文取消伝票発行フラグ         | ODR_CANCEL_SLIP_ISS_FLG        | NUMBER(1, 0)                   |          | 0                    |                                |
|  62 | 取消伝票発行日                 | ODR_CANCEL_SLIP_ISS_DATE       | DATE                           |          |                      |                                |
|  63 | 取消理由コード                 | ODR_CANCEL_CAUSE_CD            | VARCHAR2(256)                  |          |                      |                                |
|  64 | 作成日                         | CREATED_DATE                   | DATE                           |          | sysdate              |                                |
|  65 | 作成者                         | CREATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  66 | 作成プログラム名               | CREATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  67 | 更新日                         | UPDATED_DATE                   | DATE                           |          | sysdate              |                                |
|  68 | 更新者                         | UPDATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  69 | 更新プログラム名               | UPDATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  70 | 更新数                         | MODIFY_COUNT                   | NUMBER                         |          | 0                    |                                |
|  71 | オーダ数                       | ODR_QTY                        | NUMBER(18, 4)                  |          | 0                    |                                |
|  72 | 発注種別                       | PUCH_ODR_TYP                   | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  73 | 部品注文番号（備考）           | CUST_ODR_NO_REMARK             | VARCHAR2(160)                  |          |                      |                                |
|  74 | 勘定科目                       | ACCT_CD                        | VARCHAR2(96)                   |          |                      |                                |
|  75 | 初回品フラグ                   | FIRST_ITEM_FLG                 | NUMBER(2, 0)                   | Yes      | 0                    |                                |
|  76 | 初回品チェックフラグ           | FIRST_INSPEC_FLG               | NUMBER(2, 0)                   | Yes      | 0                    |                                |
|  77 | 図面バージョン                 | DRAW_CD_VER                    | VARCHAR2(100)                  |          |                      |                                |
|  78 | 予算部門                       | BUDGET_ORG_CD                  | VARCHAR2(100)                  |          |                      |                                |
|  79 | 再作成フラグ                   | REINSERT_FLG                   | NUMBER(2, 0)                   |          | 0                    |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | T_RLSD_PUCH_ODR_PKY            | PUCH_ODR_CD                              | Yes        |                                |
|   2 | T_RLSD_PUCH_ODR_IDX01          | ITEM_CD                                  |            |                                |
|   3 | T_RLSD_PUCH_ODR_IDX02          | OD_NO                                    |            |                                |
|   4 | T_RLSD_PUCH_ODR_IDX03          | VEND_CD,COMPANY_CD                       |            |                                |
|   5 | T_RLSD_PUCH_ODR_IDX04          | WORK_ODR_CD,WORK_IN_PROC_CD              |            |                                |
|   6 | T_RLSD_PUCH_ODR_IDX05          | PUCH_ODR_TYP                             |            |                                |
|   7 | T_RLSD_PUCH_ODR_IDX06          | ITEM_CD,PUCH_ODR_DLV_DATE                |            |                                |
|   8 | T_RLSD_PUCH_ODR_IDX07          | PUCH_ODR_CD,ITEM_CD,COMPANY_CD,VEND_CD,PUCH_ODR_DLV_DATE,ODR_CANCEL_SLIP_ISS_FLG,OD_NO |            |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | T_RLSD_PUCH_ODR_PKY            | PRIMARY KEY                    | PUCH_ODR_CD                    |
|   2 | SYS_C002764201                 | CHECK                          | "PUCH_ODR_CD" IS NOT NULL      |
|   3 | SYS_C002764202                 | CHECK                          | "WH_CD" IS NOT NULL            |
|   4 | SYS_C002764203                 | CHECK                          | "NON_NO_ITEM_TYP" IS NOT NULL  |
|   5 | SYS_C002764204                 | CHECK                          | "PLANT_CD" IS NOT NULL         |
|   6 | SYS_C002764205                 | CHECK                          | "PUCH_ODR_QTY" IS NOT NULL     |
|   7 | SYS_C002764206                 | CHECK                          | "UNIT_COST_TYP" IS NOT NULL    |
|   8 | SYS_C002764207                 | CHECK                          | "UNIT_COST" IS NOT NULL        |
|   9 | SYS_C002764208                 | CHECK                          | "PROCESSING_COST" IS NOT NULL  |
|  10 | SYS_C002764209                 | CHECK                          | "MATERIAL_COST" IS NOT NULL    |
|  11 | SYS_C002764210                 | CHECK                          | "OTHER_OVERHEADS" IS NOT NULL  |
|  12 | SYS_C002764211                 | CHECK                          | "DISC_AMOUNT" IS NOT NULL      |
|  13 | SYS_C002764212                 | CHECK                          | "PUCH_ODR_AMOUNT" IS NOT NULL  |
|  14 | SYS_C002764213                 | CHECK                          | "PUCH_ODR_GNR_TYP" IS NOT NULL |
|  15 | SYS_C002764214                 | CHECK                          | "PUCH_ODR_INST_SLIP_ISS_FLG" IS NOT NULL |
|  16 | SYS_C002764215                 | CHECK                          | "PUCH_ODR_STS_TYP" IS NOT NULL |
|  17 | SYS_C002764216                 | CHECK                          | "INSPC_CMPLT_FLG" IS NOT NULL  |
|  18 | SYS_C002764217                 | CHECK                          | "SPL_ITEM_TYP" IS NOT NULL     |
|  19 | SYS_C002764218                 | CHECK                          | "ACPT_INSPC_TYP" IS NOT NULL   |
|  20 | SYS_C002764219                 | CHECK                          | "INV_CTRL_FLG" IS NOT NULL     |
|  21 | SYS_C002764220                 | CHECK                          | "DETAIL_NO" IS NOT NULL        |
|  22 | SYS_C002764221                 | CHECK                          | "EXCH_RATE" IS NOT NULL        |
|  23 | SYS_C002764222                 | CHECK                          | "TAX_RATE_1" IS NOT NULL       |
|  24 | SYS_C002764223                 | CHECK                          | "TAX_RATE_2" IS NOT NULL       |
|  25 | SYS_C002764224                 | CHECK                          | "TAX_RATE_3" IS NOT NULL       |
|  26 | SYS_C002764225                 | CHECK                          | "NET_AMOUNT" IS NOT NULL       |
|  27 | SYS_C002764226                 | CHECK                          | "TAX_AMOUNT_1" IS NOT NULL     |
|  28 | SYS_C002764227                 | CHECK                          | "TAX_AMOUNT_2" IS NOT NULL     |
|  29 | SYS_C002764228                 | CHECK                          | "TAX_AMOUNT_3" IS NOT NULL     |
|  30 | SYS_C002764229                 | CHECK                          | "AMOUNT_INCLUDE_TAX" IS NOT NULL |
|  31 | SYS_C002764230                 | CHECK                          | "HOME_CUR_AMOUNT" IS NOT NULL  |
|  32 | SYS_C002764231                 | CHECK                          | "TAX_ROUND_TYP" IS NOT NULL    |
|  33 | SYS_C002764232                 | CHECK                          | "NON_NO_ITEM_FLG" IS NOT NULL  |
|  34 | SYS_C002764233                 | CHECK                          | "PUCH_ODR_EDI_ISS_FLG" IS NOT NULL |
|  35 | SYS_C002764234                 | CHECK                          | "PUCH_ODR_FAX_ISS_FLG" IS NOT NULL |
|  36 | SYS_C002764235                 | CHECK                          | "PUCH_ODR_MAIL_ISS_FLG" IS NOT NULL |
|  37 | SYS_C002764236                 | CHECK                          | "ODR_CANCEL_SLIP_ISS_FLG" IS NOT NULL |
|  38 | SYS_C002764237                 | CHECK                          | "CREATED_DATE" IS NOT NULL     |
|  39 | SYS_C002764238                 | CHECK                          | "CREATED_BY" IS NOT NULL       |
|  40 | SYS_C002764239                 | CHECK                          | "CREATED_PRG_NM" IS NOT NULL   |
|  41 | SYS_C002764240                 | CHECK                          | "UPDATED_DATE" IS NOT NULL     |
|  42 | SYS_C002764241                 | CHECK                          | "UPDATED_BY" IS NOT NULL       |
|  43 | SYS_C002764242                 | CHECK                          | "UPDATED_PRG_NM" IS NOT NULL   |
|  44 | SYS_C002764243                 | CHECK                          | "MODIFY_COUNT" IS NOT NULL     |
|  45 | SYS_C002764244                 | CHECK                          | "ODR_QTY" IS NOT NULL          |
|  46 | SYS_C002764245                 | CHECK                          | "PUCH_ODR_TYP" IS NOT NULL     |
|  47 | SYS_C002764246                 | CHECK                          | "FIRST_ITEM_FLG" IS NOT NULL   |
|  48 | SYS_C002764247                 | CHECK                          | "FIRST_INSPEC_FLG" IS NOT NULL |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | T_RLSD_PUCH_ODR_FKY02          | WH_CD                                    | EXPJ2.M_WH                     | WH_CD                                    |              |              |
|   2 | T_RLSD_PUCH_ODR_FKY03          | COMPANY_CD,VEND_CD                       | EXPJ2.M_VEND_CTRL              | COMPANY_CD,VEND_CD                       |              |              |
|   3 | T_RLSD_PUCH_ODR_FKY04          | PLANT_CD                                 | EXPJ2.M_PLANT                  | PLANT_CD                                 |              |              |
|   4 | T_RLSD_PUCH_ODR_FKY06          | WORK_ODR_CD,WORK_IN_PROC_CD              | EXPJ2.T_WORK_IN_PROC_BY_PROC   | WORK_ODR_CD,WORK_IN_PROC_CD              |              |              |
|   5 | T_RLSD_PUCH_ODR_FKY07          | OD_NO                                    | EXPJ2.T_OD                     | OD_NO                                    |              |              |
|   6 | T_RLSD_PUCH_ODR_FKY08          | TAX_CD                                   | EXPJ2.M_TAX                    | TAX_CD                                   |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | T_ACPT_RSLT_FKY01              | PUCH_ODR_CD                              | EXPJ2.T_ACPT_RSLT              | PUCH_ODR_CD                              | CASCADE      |              |
|   2 | T_ISSUE_INST_FKY04             | PUCH_ODR_CD                              | EXPJ2.T_ISSUE_INST             | PUCH_ODR_CD                              |              |              |



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_T_RLSD_PUCH_ODR10          | Insert,Update                            | Before row           |                                |
|   2 | TRG_T_RLSD_PUCH_ODR11          | Insert,Update                            | Before row           |                                |
|   3 | TRG_T_RLSD_PUCH_ODR22          | Insert,Update                            | Before row           |                                |
|   4 | TRG_T_RLSD_PUCH_ODR24          | Insert,Update                            | Before row           |                                |
|   5 | TRG_T_RLSD_PUCH_ODR25          | Insert,Update                            | Before row           |                                |
|   6 | TRG_T_RLSD_PUCH_ODR28          | Insert,Update                            | Before row           |                                |
|   7 | TRG_T_RLSD_PUCH_ODR29          | Insert,Update                            | Before row           |                                |
|   8 | TRG_T_RLSD_PUCH_ODR39          | Insert,Update                            | Before row           |                                |
|   9 | TRG_T_RLSD_PUCH_ODR54          | Insert,Update                            | Before row           |                                |
|  10 | TRG_T_RLSD_PUCH_ODR56          | Insert,Update                            | Before row           |                                |
|  11 | TRG_T_RLSD_PUCH_ODR58          | Insert,Update                            | Before row           |                                |
|  12 | TRG_T_RLSD_PUCH_ODR_N01        | Insert                                   | Before row           |                                |
|  13 | TRG_T_RLSD_PUCH_ODR_N02        | Update                                   | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | EXPJ2                                                                                                |
|   2 | TABLE_NAME                     | T_RLSD_PUCH_ODR                                                                                      |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 287309824                                                                                            |
|  12 | NEXT_EXTENT                    |                                                                                                      |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 767682                                                                                               |
|  21 | BLOCKS                         | 33700                                                                                                |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 301                                                                                                  |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 767682                                                                                               |
|  33 | LAST_ANALYZED                  | 2025/07/24 22:17:02                                                                                  |
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


