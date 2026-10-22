---
出典: 福原つながるプロジェクト_課題管理表.xlsm の「課題」シート No.380
シート: 課題
番号: No.380
区分: TODO
件名: Oracle Base Database Service (BaseDB) - Oracle Database、Grid Infrastructure - 2026年7月四半期リリースアップデート (RU)
発生部門: DAIKO
発生日: 2026-07-27
完了日: 2026-10-09
状況: 完了
---
# 課題No.380 Oracle Base Database Service (BaseDB) - Oracle Database、Grid Infrastructure - 2026年7月四半期リリースアップデート (RU)

## 内容

メール「Oracle Base Database Service (BaseDB) for fukuharaseiki : [5e0ed9de]」(7/22(水) 8:08)

急速に台頭するAIを活用したサイバーセキュリティ脅威からお客様を保護するため、OracleはOracle Database Security MOS Note PNEWS3015およびSecurity Blogでセキュリティガイダンスを更新しました。最新の四半期リリースアップデート（RU）が利用可能になりました。Oracleは、お客様が最新の四半期リリースアップデート（RU）をデータベース環境に適用することを強く推奨します。

## 対処・対策・回答案

2026/10/02 ○○
作業完了、○○さん端末で問題ないことを確認済。
次回会議までに確認いただく

2026/09/30　○○
instantclient_21_22フォルダをDLRUNでコピーできなかったため、
instantclient_12cフォルダの中身を21_22用に変更し、DLRUNの取得対象とすることで対応しようと思います。
特に福原精機様側での作業はございません。（DLRUN参照元を入れ替える作業のみ）
○○様とご相談のうえ、10/1 10:00～○○さんを交えて作業を進めさせていただきます。

2026/09/18 ○○
9/30 10時～　本番環境の作業開始します。

2026/09/17 PFW○○
OT2環境のiniファイルが更新されていることと、instantclient_21_22の存在を確認。マスタや手配の参照、更新とレポクリ出力を確認しました。
特に問題はありませんでした。本番リリースをお願いします。

2026/09/14　○○
PFW_OT2で接続確認をお願いいたします。

2026/09/10 ○○
PFW_OT2のEXEフォルダを最新化しました。
（コピペミス等があるとrBOM起動できなくなるので）PFW_OT2で起動までできるかを確認いただいてから本番も対応しようと思います。
以下のメモ帳をご確認ください。
https://all-daikodenshi.box.com/s/d7ba7oldcgse2onwk2k3u7wzhxe5yuqf
（他簡単な方法があれば検討したい）

2026/09/08 ○○
作業できておりません、リスケをさせてください。

2026/09/01 打合せ
instantclientの64bit対応の方針について確認する⇒本社
⇒rBOM V4.1からは64bitのinstantclientに対応されているようですが、
福原精機様バージョンのV4.0.4は未対応のようです。
正式に対応する場合は、rBOMを64bit版でコンパイルしなおす作業が必要とのこと。
（要調査）

2026/08/27　○○
DXT社内環境で21c（32bit版）で動作することを確認済。
現地サーバ側の環境は8/31に実施予定。
※各クライアント側の設定が必要

2026/08/04　打合せ
instant client26aiがrBOM_EXEに対応しているかを確認する
⇒instant client26aiはrBOMに非対応でした。

2026/07/28　○○
お知らせを確認しました。概要を下記に記載します。
＜サーバ＞
19c以下のバージョン⇒19cに上げること
（問題なし）
＜クライアント＞
DBに接続するOracleClientを
26ai用に変更を推奨する
（対応必要）
とのことです。

詳細は8月に確認いたします。

＜メモ＞
・Instant Clientダウンロード↓
https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html

・Windows用のOracleClientは19cまでのようです。（AIからの回答ですが。）
以降は上記のInstantClientを利用するように、とのこと。

## 結果（クローズ時）

2026/10/9 打合せ
打合せにてクローズ
