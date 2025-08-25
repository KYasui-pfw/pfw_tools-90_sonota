# 品目 (M_ITEM)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | EXPJ2                                                                                                |
| 物理テーブル名                 | M_ITEM                                                                                               |
| 論理テーブル名                 | 品目                                                                                                 |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/07/29                                                                                           |
| RDBMS                          | Oracle Database 10g Release 10.2.0.1.0 - Production 10.2.0.1.0                                       |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 | 品目番号                       | ITEM_CD                        | VARCHAR2(100)                  | Yes (PK) |                      |                                |
|   2 | 品目名                         | ITEM_NAME                      | VARCHAR2(160)                  |          |                      |                                |
|   3 | 図面番号                       | DRAW_CD                        | VARCHAR2(100)                  |          |                      |                                |
|   4 | 規格                           | SPEC                           | VARCHAR2(320)                  |          |                      |                                |
|   5 | レベル番号                     | HIGH_LEVEL_NO                  | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|   6 | 品目手配区分                   | MRP_ODR_TYP                    | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|   7 | 品目内外作区分                 | OUTSIDE_TYP                    | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|   8 | 荷姿管理フラグ                 | STOCK_UNIT_FLG                 | NUMBER(1, 0)                   | Yes      | 2                    |                                |
|   9 | 計量単位                       | STOCK_UNIT                     | VARCHAR2(48)                   |          |                      |                                |
|  10 | 荷姿計量単位                   | PKG_UNIT                       | VARCHAR2(48)                   |          |                      |                                |
|  11 | 荷姿単位数                     | PKG_UNIT_QTY                   | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  12 | 在庫数単位区分                 | UNIT_QTY_TYP                   | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  13 | 品目手配リードタイム           | ODR_LT                         | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  14 | 品目固定分リードタイム         | FIXED_LT                       | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  15 | 品目比例分リードタイム         | PROP_LT                        | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  16 | 安全日数                       | SAFETY_LT                      | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  17 | 払出リードタイム               | ISSUE_LT                       | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  18 | 品目比例分ロットサイズ         | PROP_LOT_SIZE                  | NUMBER(18, 4)                  | Yes      | 1                    |                                |
|  19 | 品目仕損率                     | ITEM_SPOIL                     | NUMBER(9, 4)                   | Yes      | 0                    |                                |
|  20 | 安全在庫量                     | SAFETY_STOCK                   | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  21 | ロットまとめ区分               | LOT_SIZING_TYP                 | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  22 | 最大まとめ期間                 | MAX_PERIOD                     | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  23 | 最大手配数                     | MAX_ODR_QTY                    | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  24 | 発注点在庫数                   | ODR_POINT                      | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  25 | 定量発注数                     | FIXED_ODR_QTY                  | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  26 | 最小手配数                     | MIN_ODR_QTY                    | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  27 | まるめ単位                     | MUL_ODR_QTY                    | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  28 | 出庫区分                       | ISSUE_TYP                      | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  29 | MPS品目フラグ                  | MPS_FLG                        | NUMBER(1, 0)                   | Yes      | 0                    |                                |
|  30 | 受入検査区分                   | ACPT_INSPC_TYP                 | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  31 | 製品区分                       | PRODUCT_TYP                    | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  32 | 作業区コード                   | CLASIFICATION_CD               | VARCHAR2(100)                  |          |                      |                                |
|  33 | 単位重量                       | UNIT_WEIGHT                    | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  34 | 棚卸区分                       | ABC_TYP                        | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  35 | 作業実績区分                   | OPR_RSLT_TYP                   | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  36 | 受給品区分                     | SPL_ITEM_TYP                   | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  37 | 消費税コード                   | TAX_CD                         | VARCHAR2(100)                  |          |                      |                                |
|  38 | カレンダ番号                   | CAL_NO                         | NUMBER(6, 0)                   |          | 0                    |                                |
|  39 | 作成日                         | CREATED_DATE                   | DATE                           |          | sysdate              |                                |
|  40 | 作成者                         | CREATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  41 | 作成プログラム名               | CREATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  42 | 更新日                         | UPDATED_DATE                   | DATE                           |          | sysdate              |                                |
|  43 | 更新者                         | UPDATED_BY                     | VARCHAR2(100)                  |          | 'SYSTEM'             |                                |
|  44 | 更新プログラム名               | UPDATED_PRG_NM                 | VARCHAR2(120)                  |          | 'SYSTEM'             |                                |
|  45 | 更新数                         | MODIFY_COUNT                   | NUMBER                         | Yes      | 0                    |                                |
|  46 | 指示書構成表示フラグ           | U_SLIP_PS_OUT_FLG              | NUMBER(1, 0)                   | Yes      | 1                    |                                |
|  47 | 作業指示書出力フラグ           | U_OPR_INST_SLIP_FLG            | NUMBER(1, 0)                   | Yes      | 1                    |                                |
|  48 | E-BOM品目番号                  | E_BOM_ITEM_CD                  | VARCHAR2(200)                  |          |                      |                                |
|  49 | 工場コード                     | PLANT_CD                       | VARCHAR2(8)                    |          | 'E'                  |                                |
|  50 | 借方勘定科目(買掛管理)         | AP_DR_ACCT_CD                  | VARCHAR2(96)                   |          | '[製]当材料仕１'     |                                |
|  51 | 借方補助科目(買掛管理)         | AP_DR_SUB_ACCT_CD              | VARCHAR2(96)                   |          |                      |                                |
|  52 | 貸方勘定科目(買掛管理)         | AP_CR_ACCT_CD                  | VARCHAR2(96)                   |          | '買掛金'             |                                |
|  53 | 貸方補助科目(買掛管理)         | AP_CR_SUB_ACCT_CD              | VARCHAR2(96)                   |          |                      |                                |
|  54 | 借方勘定科目(売掛管理)         | AR_DR_ACCT_CD                  | VARCHAR2(96)                   |          | '売掛金'             |                                |
|  55 | 借方補助科目(売掛管理)         | AR_DR_SUB_ACCT_CD              | VARCHAR2(96)                   |          |                      |                                |
|  56 | 貸方勘定科目(売掛管理)         | AR_CR_ACCT_CD                  | VARCHAR2(96)                   |          | '売上商品（部品）'   |                                |
|  57 | 貸方補助科目(売掛管理)         | AR_CR_SUB_ACCT_CD              | VARCHAR2(96)                   |          |                      |                                |
|  58 | CAT                            | ATTR_5                         | VARCHAR2(200)                  |          |                      |                                |
|  59 | 設計分類                       | ATTR_4                         | VARCHAR2(200)                  |          |                      |                                |
|  60 | 熱処理                         | HEAT_CD                        | VARCHAR2(300)                  |          |                      |                                |
|  61 | 表面処理                       | SURFACE_CD                     | VARCHAR2(300)                  |          |                      |                                |
|  62 | 材質                           | MATERIAL_CD                    | VARCHAR2(300)                  |          |                      |                                |
|  63 | 棚卸区分１                     | INV_TYP_1                      | NUMBER(2, 0)                   | Yes      | 0                    |                                |
|  64 | 棚卸区分２                     | INV_TYP_2                      | NUMBER(1, 0)                   | Yes      | 1                    |                                |
|  65 | 棚番                           | INV_NO_E                       | VARCHAR2(200)                  |          |                      |                                |
|  66 | 担当メモ                       | INV_NO_W                       | VARCHAR2(200)                  |          |                      |                                |
|  67 | メッセージ                     | INV_NO_B                       | VARCHAR2(200)                  |          |                      |                                |
|  68 | 勘定科目                       | ACCT_CD                        | VARCHAR2(96)                   |          |                      |                                |
|  69 | 金型有無                       | KANAGATA_UMU                   | NUMBER(1, 0)                   | Yes      | 0                    |                                |
|  70 | PDM品目番号                    | PDM_ITEM_CD                    | VARCHAR2(200)                  |          |                      |                                |
|  71 | メーカー／型番                 | MAKER_MODEL                    | VARCHAR2(320)                  |          |                      |                                |
|  72 | 品目バージョン                 | ITEM_VERSION                   | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  73 | 外作用品目手配リードタイム     | PUCH_ODR_LT                    | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  74 | 外作用品目固定分リードタイム   | PUCH_FIXED_LT                  | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  75 | 外作用品目比例分リードタイム   | PUCH_PROP_LT                   | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  76 | 外作用安全日数                 | PUCH_SAFETY_LT                 | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  77 | 外作用払出リードタイム         | PUCH_ISSUE_LT                  | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  78 | 払出先                         | ISSUE_SPACE                    | VARCHAR2(2)                    |          | NULL                 |                                |
|  79 | 新部品確認フラグ               | ITEM_INSPECT_FLG               | NUMBER(2, 0)                   | Yes      | 0                    |                                |
|  80 | 寸法Ｘ                         | SIZE_X                         | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  81 | 寸法Ｙ                         | SIZE_Y                         | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  82 | 寸法Ｚ                         | SIZE_Z                         | NUMBER(18, 4)                  | Yes      | 0                    |                                |
|  83 | クラス名                       | CLASS_NAME                     | VARCHAR2(320)                  |          |                      |                                |
|  84 | 次工程品番                     | NEXT_PROC_CD                   | VARCHAR2(100)                  |          |                      |                                |
|  85 | 内作用品目手配リードタイム     | WIP_ODR_LT                     | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  86 | 内作用品目固定分リードタイム   | WIP_FIXED_LT                   | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  87 | 内作用品目比例分リードタイム   | WIP_PROP_LT                    | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  88 | 内作用安全日数                 | WIP_SAFETY_LT                  | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  89 | 内作用払出リードタイム         | WIP_ISSUE_LT                   | NUMBER(6, 0)                   | Yes      | 0                    |                                |
|  90 | 配膳指示書抽出区分             | ISSUE_OUT_TYP                  | NUMBER(2, 0)                   | Yes      | 1                    |                                |
|  91 | 更新年数区分                   | UPD_YEARS_TYP                  | NUMBER(1, 0)                   |          | 0                    |                                |
|  92 | 内外作更新日                   | OUTSIDE_UPD_DATE               | DATE                           |          |                      |                                |
|  93 | 部品内作発注フラグ             | PARTS_INSIDE_PUCH_FLG          | NUMBER(2, 0)                   | Yes      | 0                    |                                |
|  94 | 部品内作発注フラグ更新日       | PARTS_INSIDE_UPD_DATE          | DATE                           |          |                      |                                |
|  95 | 最終出庫日                     | FINAL_ISSUE_DATE               | DATE                           |          |                      |                                |
|  96 | 再見積フラグ                   | ESTIMATE_FLG                   | NUMBER(2, 0)                   | Yes      | 0                    |                                |
|  97 | 初回品フラグ                   | FIRST_ITEM_FLG                 | NUMBER(2, 0)                   | Yes      | 0                    |                                |
|  98 | 部品出庫区分                   | PARTS_ISSUEL_TYP               | NUMBER(2, 0)                   | Yes      | 0                    |                                |
|  99 | 部品注文引当表出力フラグ       | PARTS_LIST_FLG                 | NUMBER(2, 0)                   | Yes      | 0                    |                                |
| 100 | 前回更新年数区分               | LAST_UPD_YEARS_TYP             | NUMBER(1, 0)                   |          | 0                    |                                |
| 101 | 更新年数区分更新日             | YEARS_TYP_UPD_DATE             | DATE                           |          | SYSDATE              |                                |
| 102 | 棚卸区分１更新日               | INV_TYP_1_UPD_DATE             | DATE                           |          | SYSDATE              |                                |
| 103 | 前回棚卸区分１                 | LAST_INV_TYP_1                 | NUMBER(2, 0)                   |          | 0                    |                                |
| 104 | 図面バージョン                 | DRAW_CD_VER                    | VARCHAR2(100)                  |          |                      |                                |



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|
|   1 | M_ITEM_PKY                     | ITEM_CD                                  | Yes        |                                |
|   2 | M_ITEM_IDX01                   | U_OPR_INST_SLIP_FLG                      |            |                                |
|   3 | M_ITEM_IDX02                   | E_BOM_ITEM_CD                            |            |                                |
|   4 | M_ITEM_IDX03                   | PDM_ITEM_CD                              |            |                                |
|   5 | M_ITEM_IDX04                   | NEXT_PROC_CD                             |            |                                |
|   6 | M_ITEM_IDX05                   | OUTSIDE_TYP                              |            |                                |
|   7 | M_ITEM_IDX06                   | PRODUCT_TYP                              |            |                                |
|   8 | M_ITEM_IDX07                   | PRODUCT_TYP,OUTSIDE_TYP                  |            |                                |
|   9 | M_ITEM_IDX08                   | OUTSIDE_TYP,ACCT_CD,PRODUCT_TYP          |            |                                |
|  10 | M_ITEM_IDX09                   | OUTSIDE_TYP,ACCT_CD                      |            |                                |
|  11 | M_ITEM_IDX10                   | ITEM_CD,OUTSIDE_TYP                      |            |                                |



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|
|   1 | M_ITEM_PKY                     | PRIMARY KEY                    | ITEM_CD                        |
|   2 | SYS_C002757634                 | CHECK                          | "ITEM_CD" IS NOT NULL          |
|   3 | SYS_C002757635                 | CHECK                          | "HIGH_LEVEL_NO" IS NOT NULL    |
|   4 | SYS_C002757636                 | CHECK                          | "MRP_ODR_TYP" IS NOT NULL      |
|   5 | SYS_C002757637                 | CHECK                          | "OUTSIDE_TYP" IS NOT NULL      |
|   6 | SYS_C002757638                 | CHECK                          | "STOCK_UNIT_FLG" IS NOT NULL   |
|   7 | SYS_C002757639                 | CHECK                          | "PKG_UNIT_QTY" IS NOT NULL     |
|   8 | SYS_C002757640                 | CHECK                          | "UNIT_QTY_TYP" IS NOT NULL     |
|   9 | SYS_C002757641                 | CHECK                          | "ODR_LT" IS NOT NULL           |
|  10 | SYS_C002757642                 | CHECK                          | "FIXED_LT" IS NOT NULL         |
|  11 | SYS_C002757643                 | CHECK                          | "PROP_LT" IS NOT NULL          |
|  12 | SYS_C002757644                 | CHECK                          | "SAFETY_LT" IS NOT NULL        |
|  13 | SYS_C002757645                 | CHECK                          | "ISSUE_LT" IS NOT NULL         |
|  14 | SYS_C002757646                 | CHECK                          | "PROP_LOT_SIZE" IS NOT NULL    |
|  15 | SYS_C002757647                 | CHECK                          | "ITEM_SPOIL" IS NOT NULL       |
|  16 | SYS_C002757648                 | CHECK                          | "SAFETY_STOCK" IS NOT NULL     |
|  17 | SYS_C002757649                 | CHECK                          | "LOT_SIZING_TYP" IS NOT NULL   |
|  18 | SYS_C002757650                 | CHECK                          | "MAX_PERIOD" IS NOT NULL       |
|  19 | SYS_C002757651                 | CHECK                          | "MAX_ODR_QTY" IS NOT NULL      |
|  20 | SYS_C002757652                 | CHECK                          | "ODR_POINT" IS NOT NULL        |
|  21 | SYS_C002757653                 | CHECK                          | "FIXED_ODR_QTY" IS NOT NULL    |
|  22 | SYS_C002757654                 | CHECK                          | "MIN_ODR_QTY" IS NOT NULL      |
|  23 | SYS_C002757655                 | CHECK                          | "MUL_ODR_QTY" IS NOT NULL      |
|  24 | SYS_C002757656                 | CHECK                          | "ISSUE_TYP" IS NOT NULL        |
|  25 | SYS_C002757657                 | CHECK                          | "MPS_FLG" IS NOT NULL          |
|  26 | SYS_C002757658                 | CHECK                          | "ACPT_INSPC_TYP" IS NOT NULL   |
|  27 | SYS_C002757659                 | CHECK                          | "PRODUCT_TYP" IS NOT NULL      |
|  28 | SYS_C002757660                 | CHECK                          | "UNIT_WEIGHT" IS NOT NULL      |
|  29 | SYS_C002757661                 | CHECK                          | "ABC_TYP" IS NOT NULL          |
|  30 | SYS_C002757662                 | CHECK                          | "OPR_RSLT_TYP" IS NOT NULL     |
|  31 | SYS_C002757663                 | CHECK                          | "SPL_ITEM_TYP" IS NOT NULL     |
|  32 | SYS_C002757664                 | CHECK                          | "MODIFY_COUNT" IS NOT NULL     |
|  33 | SYS_C002757665                 | CHECK                          | "U_SLIP_PS_OUT_FLG" IS NOT NULL |
|  34 | SYS_C002757666                 | CHECK                          | "U_OPR_INST_SLIP_FLG" IS NOT NULL |
|  35 | SYS_C002757667                 | CHECK                          | "INV_TYP_1" IS NOT NULL        |
|  36 | SYS_C002757668                 | CHECK                          | "INV_TYP_2" IS NOT NULL        |
|  37 | SYS_C002757669                 | CHECK                          | "KANAGATA_UMU" IS NOT NULL     |
|  38 | SYS_C002757670                 | CHECK                          | "ITEM_VERSION" IS NOT NULL     |
|  39 | SYS_C002757671                 | CHECK                          | "PUCH_ODR_LT" IS NOT NULL      |
|  40 | SYS_C002757672                 | CHECK                          | "PUCH_FIXED_LT" IS NOT NULL    |
|  41 | SYS_C002757673                 | CHECK                          | "PUCH_PROP_LT" IS NOT NULL     |
|  42 | SYS_C002757674                 | CHECK                          | "PUCH_SAFETY_LT" IS NOT NULL   |
|  43 | SYS_C002757675                 | CHECK                          | "PUCH_ISSUE_LT" IS NOT NULL    |
|  44 | SYS_C002757676                 | CHECK                          | "ITEM_INSPECT_FLG" IS NOT NULL |
|  45 | SYS_C002757677                 | CHECK                          | "SIZE_X" IS NOT NULL           |
|  46 | SYS_C002757678                 | CHECK                          | "SIZE_Y" IS NOT NULL           |
|  47 | SYS_C002757679                 | CHECK                          | "SIZE_Z" IS NOT NULL           |
|  48 | SYS_C002757680                 | CHECK                          | "WIP_ODR_LT" IS NOT NULL       |
|  49 | SYS_C002757681                 | CHECK                          | "WIP_FIXED_LT" IS NOT NULL     |
|  50 | SYS_C002757682                 | CHECK                          | "WIP_PROP_LT" IS NOT NULL      |
|  51 | SYS_C002757683                 | CHECK                          | "WIP_SAFETY_LT" IS NOT NULL    |
|  52 | SYS_C002757684                 | CHECK                          | "WIP_ISSUE_LT" IS NOT NULL     |
|  53 | SYS_C002757685                 | CHECK                          | "ISSUE_OUT_TYP" IS NOT NULL    |
|  54 | SYS_C002757686                 | CHECK                          | "PARTS_INSIDE_PUCH_FLG" IS NOT NULL |
|  55 | SYS_C002757687                 | CHECK                          | "ESTIMATE_FLG" IS NOT NULL     |
|  56 | SYS_C002757688                 | CHECK                          | "FIRST_ITEM_FLG" IS NOT NULL   |
|  57 | SYS_C002757689                 | CHECK                          | "PARTS_ISSUEL_TYP" IS NOT NULL |
|  58 | SYS_C002757690                 | CHECK                          | "PARTS_LIST_FLG" IS NOT NULL   |



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | M_ITEM_FKY01                   | TAX_CD                                   | EXPJ2.M_TAX                    | TAX_CD                                   |              |              |
|   2 | M_ITEM_FKY02                   | CAL_NO                                   | EXPJ2.M_CAL_H                  | CAL_NO                                   |              |              |



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|
|   1 | M_PS_FKY01                     | ITEM_CD                                  | EXPJ2.M_PS                     | PARENT_ITEM_CD                           | CASCADE      |              |
|   2 | M_PS_FKY02                     | ITEM_CD                                  | EXPJ2.M_PS                     | COMP_ITEM_CD                             | CASCADE      |              |



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|
|   1 | TRG_M_ITEM_U1                  | Update                                   | Before row           |                                |
|   2 | TRG_M_ITEM_U2                  | Update                                   | Before row           |                                |
|   3 | TRG_M_ITEM_U3                  | Insert,Update                            | After row            |                                |
|   4 | TRG_M_ITEM_U4                  | Update                                   | Before row           |                                |
|   5 | TRG_M_ITEM_U5                  | Update                                   | Before row           |                                |
|   6 | TRG_M_ITEM_U6                  | Insert,Update                            | Before row           |                                |



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | OWNER                          | EXPJ2                                                                                                |
|   2 | TABLE_NAME                     | M_ITEM                                                                                               |
|   3 | TABLESPACE_NAME                | USERS                                                                                                |
|   4 | CLUSTER_NAME                   |                                                                                                      |
|   5 | IOT_NAME                       |                                                                                                      |
|   6 | STATUS                         | VALID                                                                                                |
|   7 | PCT_FREE                       | 10                                                                                                   |
|   8 | PCT_USED                       |                                                                                                      |
|   9 | INI_TRANS                      | 1                                                                                                    |
|  10 | MAX_TRANS                      | 255                                                                                                  |
|  11 | INITIAL_EXTENT                 | 620756992                                                                                            |
|  12 | NEXT_EXTENT                    |                                                                                                      |
|  13 | MIN_EXTENTS                    | 1                                                                                                    |
|  14 | MAX_EXTENTS                    | 2147483645                                                                                           |
|  15 | PCT_INCREASE                   |                                                                                                      |
|  16 | FREELISTS                      |                                                                                                      |
|  17 | FREELIST_GROUPS                |                                                                                                      |
|  18 | LOGGING                        | YES                                                                                                  |
|  19 | BACKED_UP                      | N                                                                                                    |
|  20 | NUM_ROWS                       | 1428245                                                                                              |
|  21 | BLOCKS                         | 73606                                                                                                |
|  22 | EMPTY_BLOCKS                   | 0                                                                                                    |
|  23 | AVG_SPACE                      | 0                                                                                                    |
|  24 | CHAIN_CNT                      | 0                                                                                                    |
|  25 | AVG_ROW_LEN                    | 359                                                                                                  |
|  26 | AVG_SPACE_FREELIST_BLOCKS      | 0                                                                                                    |
|  27 | NUM_FREELIST_BLOCKS            | 0                                                                                                    |
|  28 | DEGREE                         |          1                                                                                           |
|  29 | INSTANCES                      |          1                                                                                           |
|  30 | CACHE                          |     N                                                                                                |
|  31 | TABLE_LOCK                     | ENABLED                                                                                              |
|  32 | SAMPLE_SIZE                    | 1428245                                                                                              |
|  33 | LAST_ANALYZED                  | 2025/07/21 22:02:26                                                                                  |
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


