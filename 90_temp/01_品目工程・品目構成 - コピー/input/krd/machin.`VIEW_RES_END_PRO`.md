# VIEW (VIEW_RES_END_PRO)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | machin                                                                                               |
| 物理テーブル名                 | VIEW_RES_END_PRO                                                                                     |
| 論理テーブル名                 | VIEW                                                                                                 |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/08/29                                                                                           |
| RDBMS                          |  5.1.56                                                                                              |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 |                                | GETSUJI                        | varchar(58)                    |          |                      |                                |
|   2 |                                | LOT_CODE                       | varchar(255)                   |          |                      |                                |
|   3 |                                | P_NAME                         | varchar(20)                    |          |                      |                                |
|   4 |                                | F_CODE                         | varchar(20)                    |          |                      |                                |
|   5 |                                | QTY                            | int(4)                         |          |                      |                                |
|   6 |                                | RESULT_END                     | varchar(5)                     |          |                      |                                |
|   7 |                                | RESULT_PROCESS                 | varchar(20)                    |          |                      |                                |
|   8 | 資源名(加工機名)               | RESULT_RES                     | varchar(30)                    |          |                      |                                |
|   9 | 資源のグループ名               | GROUP_NAME                     | varchar(30)                    |          |                      |                                |
|  10 |                                | rsv4                           | varchar(20)                    |          |                      |                                |
|  11 |                                | WI_END                         | varchar(8)                     |          |                      |                                |
|  12 |                                | ASP_END                        | varchar(5)                     |          |                      |                                |
|  13 |                                | JOB_CODE                       | varchar(255)                   |          |                      |                                |



## ソース
```
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `VIEW_RES_END_PRO` AS select substr(`VIEW_DB_INPUT_AFTER`.`rsv4`,3) AS `GETSUJI`,`VIEW_DB_INPUT_AFTER`.`lotCode` AS `LOT_CODE`,`VIEW_DB_INPUT_AFTER`.`rsv6` AS `P_NAME`,`VIEW_DB_INPUT_AFTER`.`rsv5` AS `F_CODE`,`VIEW_DB_INPUT_AFTER`.`qty` AS `QTY`,date_format(`VIEW_DB_INPUT_AFTER`.`resultEnd`,'%m/%d') AS `RESULT_END`,`VIEW_DB_INPUT_AFTER`.`processCode` AS `RESULT_PROCESS`,`MSTR_RES`.`NAME` AS `RESULT_RES`,`MSTR_RES_GROUP`.`NAME` AS `GROUP_NAME`,`VIEW_DB_INPUT_AFTER`.`rsv4` AS `rsv4`,substr(`VIEW_DB_INPUT_AFTER`.`rsv9`,6,8) AS `WI_END`,date_format(`VIEW_DB_INPUT_AFTER`.`end`,'%m/%d') AS `ASP_END`,`VIEW_DB_INPUT_AFTER`.`jobCode` AS `JOB_CODE` from (`VIEW_DB_INPUT_AFTER` left join (`MSTR_RES` left join `MSTR_RES_GROUP` on((`MSTR_RES`.`GROUP_NO` = `MSTR_RES_GROUP`.`NO`))) on((`VIEW_DB_INPUT_AFTER`.`JITSUKAKOKI` = `MSTR_RES`.`CODE`))) where (`VIEW_DB_INPUT_AFTER`.`level` = 1) order by substr(`VIEW_DB_INPUT_AFTER`.`rsv4`,3),`VIEW_DB_INPUT_AFTER`.`rsv6`,`VIEW_DB_INPUT_AFTER`.`rsv5`
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
|   3 | TABLE_NAME                     | VIEW_RES_END_PRO                                                                                     |
|   4 | VIEW_DEFINITION                | select substr(`VIEW_DB_INPUT_AFTER`.`rsv4`,3) AS `GETSUJI`,`VIEW_DB_INPUT_AFTER`.`lotCode` AS `LOT_CODE`,`VIEW_DB_INPUT_AFTER`.`rsv6` AS `P_NAME`,`VIEW_DB_INPUT_AFTER`.`rsv5` AS `F_CODE`,`VIEW_DB_INPUT_AFTER`.`qty` AS `QTY`,date_format(`VIEW_DB_INPUT_AFTER`.`resultEnd`,'%m/%d') AS `RESULT_END`,`VIEW_DB_INPUT_AFTER`.`processCode` AS `RESULT_PROCESS`,`machin`.`MSTR_RES`.`NAME` AS `RESULT_RES`,`machin`.`MSTR_RES_GROUP`.`NAME` AS `GROUP_NAME`,`VIEW_DB_INPUT_AFTER`.`rsv4` AS `rsv4`,substr(`VIEW_DB_INPUT_AFTER`.`rsv9`,6,8) AS `WI_END`,date_format(`VIEW_DB_INPUT_AFTER`.`end`,'%m/%d') AS `ASP_END`,`VIEW_DB_INPUT_AFTER`.`jobCode` AS `JOB_CODE` from (`machin`.`VIEW_DB_INPUT_AFTER` left join (`machin`.`MSTR_RES` left join `machin`.`MSTR_RES_GROUP` on((`machin`.`MSTR_RES`.`GROUP_NO` = `machin`.`MSTR_RES_GROUP`.`NO`))) on((`VIEW_DB_INPUT_AFTER`.`JITSUKAKOKI` = `machin`.`MSTR_RES`.`CODE`))) where (`VIEW_DB_INPUT_AFTER`.`level` = 1) order by substr(`VIEW_DB_INPUT_AFTER`.`rsv4`,3),`VIEW_DB_INPUT_AFTER`.`rsv6`,`VIEW_DB_INPUT_AFTER`.`rsv5` |
|   5 | CHECK_OPTION                   | NONE                                                                                                 |
|   6 | IS_UPDATABLE                   | YES                                                                                                  |
|   7 | DEFINER                        | root@localhost                                                                                       |
|   8 | SECURITY_TYPE                  | DEFINER                                                                                              |
|   9 | CHARACTER_SET_CLIENT           | utf8                                                                                                 |
|  10 | COLLATION_CONNECTION           | utf8_general_ci                                                                                      |


