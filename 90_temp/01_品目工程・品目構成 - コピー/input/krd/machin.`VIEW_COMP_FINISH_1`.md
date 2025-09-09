# VIEW (VIEW_COMP_FINISH_1)

## テーブル情報

| 項目                           | 値                                                                                                   |
|:-------------------------------|:-----------------------------------------------------------------------------------------------------|
| システム名                     |                                                                                                      |
| サブシステム名                 |                                                                                                      |
| スキーマ名                     | machin                                                                                               |
| 物理テーブル名                 | VIEW_COMP_FINISH_1                                                                                   |
| 論理テーブル名                 | VIEW                                                                                                 |
| 作成者                         | yasui                                                                                                |
| 作成日                         | 2025/08/29                                                                                           |
| RDBMS                          |  5.1.56                                                                                              |



## カラム情報

| No. | 論理名                         | 物理名                         | データ型                       | Not Null | デフォルト           | 備考                           |
|----:|:-------------------------------|:-------------------------------|:-------------------------------|:---------|:---------------------|:-------------------------------|
|   1 |                                | lotCode                        | varchar(255)                   |          |                      |                                |
|   2 |                                | status                         | varchar(1)                     |          |                      |                                |
|   3 |                                | level                          | int(2)                         |          |                      |                                |



## ソース
```
CREATE ALGORITHM=UNDEFINED DEFINER=`pfw`@`localhost` SQL SECURITY DEFINER VIEW `VIEW_COMP_FINISH_1` AS select `DATA_JOB2`.`lotCode` AS `lotCode`,`DATA_JOB2`.`status` AS `status`,`DATA_JOB2`.`level` AS `level` from (`VIEW_COMP_FINISH` join `DATA_JOB2` on((`VIEW_COMP_FINISH`.`lotCode` = `DATA_JOB2`.`lotCode`))) where (`DATA_JOB2`.`level` >= `VIEW_COMP_FINISH`.`levelMin`)
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
|   3 | TABLE_NAME                     | VIEW_COMP_FINISH_1                                                                                   |
|   4 | VIEW_DEFINITION                | select `machin`.`DATA_JOB2`.`lotCode` AS `lotCode`,`machin`.`DATA_JOB2`.`status` AS `status`,`machin`.`DATA_JOB2`.`level` AS `level` from (`machin`.`VIEW_COMP_FINISH` join `machin`.`DATA_JOB2` on((`VIEW_COMP_FINISH`.`lotCode` = `machin`.`DATA_JOB2`.`lotCode`))) where (`machin`.`DATA_JOB2`.`level` \>= `VIEW_COMP_FINISH`.`levelMin`) |
|   5 | CHECK_OPTION                   | NONE                                                                                                 |
|   6 | IS_UPDATABLE                   | YES                                                                                                  |
|   7 | DEFINER                        | pfw@localhost                                                                                        |
|   8 | SECURITY_TYPE                  | DEFINER                                                                                              |
|   9 | CHARACTER_SET_CLIENT           | utf8                                                                                                 |
|  10 | COLLATION_CONNECTION           | utf8_general_ci                                                                                      |


