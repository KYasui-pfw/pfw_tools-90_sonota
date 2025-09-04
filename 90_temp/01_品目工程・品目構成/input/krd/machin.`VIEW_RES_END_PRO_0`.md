# VIEW (VIEW_RES_END_PRO_0)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | machin                                                                                               |
| 物理テーブル名                 | VIEW_RES_END_PRO_0                                                                                   |
| 論理テーブル名                 | VIEW                                                                                                 |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/08/29                                                                                           |
| RDBMS                          |  5.1.56                                                                                              |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 |                                | rsv1                           | varchar(20)                    |          |                      |                                |
|   2 |                                | GETSUJI                        | varchar(58)                    |          |                      |                                |
|   3 |                                | P_NAME                         | varchar(20)                    |          |                      |                                |
|   4 |                                | F_CODE                         | varchar(20)                    |          |                      |                                |
|   5 |                                | RESULT_END                     | varchar(5)                     |          |                      |                                |
|   6 |                                | RESULT_PROCESS                 | varchar(20)                    |          |                      |                                |
|   7 | 資源名(加工機名)               | RESULT_RES                     | varchar(30)                    |          |                      |                                |
|   8 | 資源のグループ名               | GROUP_NAME                     | varchar(30)                    |          |                      |                                |
|   9 |                                | rsv4                           | varchar(20)                    |          |                      |                                |
|  10 |                                | WI_END                         | varchar(8)                     |          |                      |                                |
|  11 |                                | ASP_END                        | varchar(5)                     |          |                      |                                |
|  12 |                                | DELIVERY                       | varchar(5)                     |          |                      |                                |
|  13 |                                | JOB_CODE                       | varchar(255)                   |          |                      |                                |



## ソース
```
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `VIEW_RES_END_PRO_0` AS select `DATA_LOT`.`rsv1` AS `rsv1`,`VIEW_RES_END_PRO`.`GETSUJI` AS `GETSUJI`,`VIEW_RES_END_PRO`.`P_NAME` AS `P_NAME`,`VIEW_RES_END_PRO`.`F_CODE` AS `F_CODE`,`VIEW_RES_END_PRO`.`RESULT_END` AS `RESULT_END`,`VIEW_RES_END_PRO`.`RESULT_PROCESS` AS `RESULT_PROCESS`,`VIEW_RES_END_PRO`.`RESULT_RES` AS `RESULT_RES`,`VIEW_RES_END_PRO`.`GROUP_NAME` AS `GROUP_NAME`,`VIEW_RES_END_PRO`.`rsv4` AS `rsv4`,`VIEW_RES_END_PRO`.`WI_END` AS `WI_END`,`VIEW_RES_END_PRO`.`ASP_END` AS `ASP_END`,date_format(`DATA_LOT`.`let`,'%m/%d') AS `DELIVERY`,`VIEW_RES_END_PRO`.`JOB_CODE` AS `JOB_CODE` from (`VIEW_RES_END_PRO` left join `DATA_LOT` on((`VIEW_RES_END_PRO`.`LOT_CODE` = `DATA_LOT`.`lotCode`))) group by `DATA_LOT`.`rsv1`,`VIEW_RES_END_PRO`.`GETSUJI`,`VIEW_RES_END_PRO`.`P_NAME`,`VIEW_RES_END_PRO`.`F_CODE`,`VIEW_RES_END_PRO`.`RESULT_END`,`VIEW_RES_END_PRO`.`RESULT_PROCESS`,`VIEW_RES_END_PRO`.`RESULT_RES`,`VIEW_RES_END_PRO`.`GROUP_NAME`,`VIEW_RES_END_PRO`.`rsv4`,`VIEW_RES_END_PRO`.`WI_END`
```



## インデックス情報

| No. | インデックス名                 | カラムリスト                             | ユニーク   | オプション                     | 
|----:|:-------------------------------|:-----------------------------------------|:-----------|:-------------------------------|



## 制約情報

| No. | 制約名                         | 種類                           | 制約定義                       |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|



## 外部キー情報

| No. | 外部キー名                     | カラムリスト                             | 参照先                         | 参照先カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## 外部キー情報(PK側)

| No. | 外部キー名                     | カラムリスト                             | 参照元                         | 参照元カラムリスト                       | ON DELETE    | ON UPDATE    |
|----:|:-------------------------------|:-----------------------------------------|:-------------------------------|:-----------------------------------------|:-------------|:-------------|



## トリガー情報

| No. | トリガー名                     | イベント                                 | タイミング           | 条件                           |
|----:|:-------------------------------|:-----------------------------------------|:---------------------|:-------------------------------|



## RDBMS固有の情報

| No. | プロパティ名                   | プロパティ値                                                                                         |
|----:|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
|   1 | TABLE_CATALOG                  |                                                                                                      |
|   2 | TABLE_SCHEMA                   | machin                                                                                               |
|   3 | TABLE_NAME                     | VIEW_RES_END_PRO_0                                                                                   |
|   4 | VIEW_DEFINITION                | select `machin`.`DATA_LOT`.`rsv1` AS `rsv1`,`VIEW_RES_END_PRO`.`GETSUJI` AS `GETSUJI`,`VIEW_RES_END_PRO`.`P_NAME` AS `P_NAME`,`VIEW_RES_END_PRO`.`F_CODE` AS `F_CODE`,`VIEW_RES_END_PRO`.`RESULT_END` AS `RESULT_END`,`VIEW_RES_END_PRO`.`RESULT_PROCESS` AS `RESULT_PROCESS`,`VIEW_RES_END_PRO`.`RESULT_RES` AS `RESULT_RES`,`VIEW_RES_END_PRO`.`GROUP_NAME` AS `GROUP_NAME`,`VIEW_RES_END_PRO`.`rsv4` AS `rsv4`,`VIEW_RES_END_PRO`.`WI_END` AS `WI_END`,`VIEW_RES_END_PRO`.`ASP_END` AS `ASP_END`,date_format(`machin`.`DATA_LOT`.`let`,'%m/%d') AS `DELIVERY`,`VIEW_RES_END_PRO`.`JOB_CODE` AS `JOB_CODE` from (`machin`.`VIEW_RES_END_PRO` left join `machin`.`DATA_LOT` on((`VIEW_RES_END_PRO`.`LOT_CODE` = `machin`.`DATA_LOT`.`lotCode`))) group by `machin`.`DATA_LOT`.`rsv1`,`VIEW_RES_END_PRO`.`GETSUJI`,`VIEW_RES_END_PRO`.`P_NAME`,`VIEW_RES_END_PRO`.`F_CODE`,`VIEW_RES_END_PRO`.`RESULT_END`,`VIEW_RES_END_PRO`.`RESULT_PROCESS`,`VIEW_RES_END_PRO`.`RESULT_RES`,`VIEW_RES_END_PRO`.`GROUP_NAME`,`VIEW_RES_END_PRO`.`rsv4`,`VIEW_RES_END_PRO`.`WI_END` |
|   5 | CHECK_OPTION                   | NONE                                                                                                 |
|   6 | IS_UPDATABLE                   | NO                                                                                                   |
|   7 | DEFINER                        | root@localhost                                                                                       |
|   8 | SECURITY_TYPE                  | DEFINER                                                                                              |
|   9 | CHARACTER_SET_CLIENT           | utf8                                                                                                 |
|  10 | COLLATION_CONNECTION           | utf8_general_ci                                                                                      |


