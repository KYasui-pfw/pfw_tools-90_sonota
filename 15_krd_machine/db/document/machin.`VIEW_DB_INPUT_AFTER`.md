# VIEW (VIEW_DB_INPUT_AFTER)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | machin                                                                                               |
| 物理テーブル名                 | VIEW_DB_INPUT_AFTER                                                                                  |
| 論理テーブル名                 | VIEW                                                                                                 |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/11/22                                                                                           |
| RDBMS                          |  5.1.56                                                                                              |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 |                                | jobCode                        | varchar(255)                   |          |                      |                                |
|   2 |                                | lotCode                        | varchar(255)                   |          |                      |                                |
|   3 |                                | mainResCode                    | varchar(10)                    |          |                      |                                |
|   4 |                                | itemCode                       | varchar(255)                   |          |                      |                                |
|   5 |                                | start                          | datetime                       |          |                      |                                |
|   6 |                                | end                            | datetime                       |          |                      |                                |
|   7 |                                | intStart                       | datetime                       |          |                      |                                |
|   8 |                                | intEnd                         | datetime                       |          |                      |                                |
|   9 |                                | time_m                         | decimal(15,4)                  |          |                      |                                |
|  10 |                                | qty                            | int(4)                         |          |                      |                                |
|  11 |                                | resultQty                      | int(4)                         |          |                      |                                |
|  12 |                                | status                         | varchar(1)                     |          |                      |                                |
|  13 |                                | assignFlag                     | varchar(1)                     |          |                      |                                |
|  14 |                                | SETU_F                         | varchar(18)                    |          |                      |                                |
|  15 |                                | STATUSSTR                      | varchar(4)                     | Yes      |                      |                                |
|  16 |                                | itemCode2                      | varchar(17)                    |          |                      |                                |
|  17 |                                | rsv4                           | varchar(20)                    |          |                      |                                |
|  18 |                                | rsv5                           | varchar(20)                    |          |                      |                                |
|  19 |                                | rsv6                           | varchar(20)                    |          |                      |                                |
|  20 |                                | rsv8                           | varchar(20)                    |          |                      |                                |
|  21 |                                | rsv9                           | varchar(20)                    |          |                      |                                |
|  22 |                                | rsv10                          | varchar(20)                    |          |                      |                                |
|  23 |                                | processCode                    | varchar(20)                    |          |                      |                                |
|  24 |                                | JITSUKAKOKI                    | varchar(20)                    |          |                      |                                |
|  25 |                                | resultEnd                      | datetime                       |          |                      |                                |
|  26 |                                | level                          | int(2)                         |          |                      |                                |



## ソース
```
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `VIEW_DB_INPUT_AFTER` AS select distinct `DATA_JOB`.`jobCode` AS `jobCode`,`DATA_JOB`.`lotCode` AS `lotCode`,`DATA_JOB`.`mainResCode` AS `mainResCode`,`DATA_JOB`.`itemCode` AS `itemCode`,`DATA_JOB`.`start` AS `start`,`DATA_JOB`.`end` AS `end`,`DATA_JOB`.`intStart` AS `intStart`,`DATA_JOB`.`intEnd` AS `intEnd`,((`DATA_JOB`.`time` / 60) + 0.5) AS `time_m`,`DATA_JOB`.`qty` AS `qty`,`DATA_JOB`.`resultQty` AS `resultQty`,`DATA_JOB`.`status` AS `status`,`DATA_JOB`.`assignFlag` AS `assignFlag`,rtrim(left(`DATA_JOB`.`itemCode`,18)) AS `SETU_F`,if((`DATA_JOB`.`status` = 'C'),'SUMI','') AS `STATUSSTR`,trim(left(`DATA_JOB`.`itemCode`,17)) AS `itemCode2`,`DATA_JOB`.`rsv4` AS `rsv4`,`DATA_JOB`.`rsv5` AS `rsv5`,`DATA_JOB`.`rsv6` AS `rsv6`,`DATA_JOB`.`rsv8` AS `rsv8`,`DATA_JOB`.`rsv9` AS `rsv9`,`DATA_JOB`.`rsv10` AS `rsv10`,`DATA_JOB`.`processCode` AS `processCode`,if(((`DATA_JOB`.`rsv10` = '') or isnull(`DATA_JOB`.`rsv10`)),`DATA_JOB`.`mainResCode`,`DATA_JOB`.`rsv10`) AS `JITSUKAKOKI`,`DATA_JOB`.`resultEnd` AS `resultEnd`,`DATA_JOB`.`level` AS `level` from `DATA_JOB`
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
|   3 | TABLE_NAME                     | VIEW_DB_INPUT_AFTER                                                                                  |
|   4 | VIEW_DEFINITION                | select distinct `machin`.`DATA_JOB`.`jobCode` AS `jobCode`,`machin`.`DATA_JOB`.`lotCode` AS `lotCode`,`machin`.`DATA_JOB`.`mainResCode` AS `mainResCode`,`machin`.`DATA_JOB`.`itemCode` AS `itemCode`,`machin`.`DATA_JOB`.`start` AS `start`,`machin`.`DATA_JOB`.`end` AS `end`,`machin`.`DATA_JOB`.`intStart` AS `intStart`,`machin`.`DATA_JOB`.`intEnd` AS `intEnd`,((`machin`.`DATA_JOB`.`time` / 60) + 0.5) AS `time_m`,`machin`.`DATA_JOB`.`qty` AS `qty`,`machin`.`DATA_JOB`.`resultQty` AS `resultQty`,`machin`.`DATA_JOB`.`status` AS `status`,`machin`.`DATA_JOB`.`assignFlag` AS `assignFlag`,rtrim(left(`machin`.`DATA_JOB`.`itemCode`,18)) AS `SETU_F`,if((`machin`.`DATA_JOB`.`status` = 'C'),'SUMI','') AS `STATUSSTR`,trim(left(`machin`.`DATA_JOB`.`itemCode`,17)) AS `itemCode2`,`machin`.`DATA_JOB`.`rsv4` AS `rsv4`,`machin`.`DATA_JOB`.`rsv5` AS `rsv5`,`machin`.`DATA_JOB`.`rsv6` AS `rsv6`,`machin`.`DATA_JOB`.`rsv8` AS `rsv8`,`machin`.`DATA_JOB`.`rsv9` AS `rsv9`,`machin`.`DATA_JOB`.`rsv10` AS `rsv10`,`machin`.`DATA_JOB`.`processCode` AS `processCode`,if(((`machin`.`DATA_JOB`.`rsv10` = '') or isnull(`machin`.`DATA_JOB`.`rsv10`)),`machin`.`DATA_JOB`.`mainResCode`,`machin`.`DATA_JOB`.`rsv10`) AS `JITSUKAKOKI`,`machin`.`DATA_JOB`.`resultEnd` AS `resultEnd`,`machin`.`DATA_JOB`.`level` AS `level` from `machin`.`DATA_JOB` |
|   5 | CHECK_OPTION                   | NONE                                                                                                 |
|   6 | IS_UPDATABLE                   | NO                                                                                                   |
|   7 | DEFINER                        | root@localhost                                                                                       |
|   8 | SECURITY_TYPE                  | DEFINER                                                                                              |
|   9 | CHARACTER_SET_CLIENT           | utf8                                                                                                 |
|  10 | COLLATION_CONNECTION           | utf8_general_ci                                                                                      |


