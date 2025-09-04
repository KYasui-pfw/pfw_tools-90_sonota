# VIEW (View_Data_Job)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | machin                                                                                               |
| 物理テーブル名                 | View_Data_Job                                                                                        |
| 論理テーブル名                 | VIEW                                                                                                 |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/08/29                                                                                           |
| RDBMS                          |  5.1.56                                                                                              |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 |                                | lotCode                        | varchar(255)                   |          |                      |                                |
|   2 |                                | rsv5                           | varchar(20)                    |          |                      |                                |
|   3 |                                | rsv6                           | varchar(20)                    |          |                      |                                |
|   4 |                                | qty                            | int(4)                         |          |                      |                                |
|   5 |                                | rsv4                           | varchar(58)                    |          |                      |                                |
|   6 |                                | processCode                    | varchar(20)                    |          |                      |                                |
|   7 |                                | resultEnd                      | varchar(10)                    |          |                      |                                |



## ソース
```
CREATE ALGORITHM=UNDEFINED DEFINER=`pfw`@`localhost` SQL SECURITY DEFINER VIEW `View_Data_Job` AS select `DATA_JOB`.`lotCode` AS `lotCode`,`DATA_JOB`.`rsv5` AS `rsv5`,`DATA_JOB`.`rsv6` AS `rsv6`,`DATA_JOB`.`qty` AS `qty`,substr(`DATA_JOB`.`rsv4`,3) AS `rsv4`,`DATA_JOB`.`processCode` AS `processCode`,date_format(`DATA_JOB`.`resultEnd`,'%Y/%m/%d') AS `resultEnd` from `DATA_JOB` where ((`DATA_JOB`.`level` = 1) and (`DATA_JOB`.`mainResCode` <> '000'))
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
|   3 | TABLE_NAME                     | View_Data_Job                                                                                        |
|   4 | VIEW_DEFINITION                | select `machin`.`DATA_JOB`.`lotCode` AS `lotCode`,`machin`.`DATA_JOB`.`rsv5` AS `rsv5`,`machin`.`DATA_JOB`.`rsv6` AS `rsv6`,`machin`.`DATA_JOB`.`qty` AS `qty`,substr(`machin`.`DATA_JOB`.`rsv4`,3) AS `rsv4`,`machin`.`DATA_JOB`.`processCode` AS `processCode`,date_format(`machin`.`DATA_JOB`.`resultEnd`,'%Y/%m/%d') AS `resultEnd` from `machin`.`DATA_JOB` where ((`machin`.`DATA_JOB`.`level` = 1) and (`machin`.`DATA_JOB`.`mainResCode` \<\> '000')) |
|   5 | CHECK_OPTION                   | NONE                                                                                                 |
|   6 | IS_UPDATABLE                   | YES                                                                                                  |
|   7 | DEFINER                        | pfw@localhost                                                                                        |
|   8 | SECURITY_TYPE                  | DEFINER                                                                                              |
|   9 | CHARACTER_SET_CLIENT           | utf8                                                                                                 |
|  10 | COLLATION_CONNECTION           | utf8_general_ci                                                                                      |


