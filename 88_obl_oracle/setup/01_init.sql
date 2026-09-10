-- ============================================================
--  初回のDB作成直後に1回だけ自動実行される（/opt/oracle/scripts/setup）
--  実行コンテキストは「CDBルートに sqlplus / as sysdba」なので、
--  先頭で PDB へ切り替える必要がある。
-- ============================================================

ALTER SESSION SET CONTAINER=FREEPDB1;

-- impdp が dmp を読むディレクトリ（compose の ./dmp をマウントしている）
CREATE OR REPLACE DIRECTORY dmpdir AS '/opt/oracle/dmp';

-- ★2年運用の最重要ポイント
--   DEFAULT プロファイルは PASSWORD_LIFE_TIME=180日 / FAILED_LOGIN_ATTEMPTS=10 のため、
--   放置すると半年後に ORA-28001（失効）、リトライ数回で ORA-28000（ロック）になる。
--   さらに PASSWORD_VERIFY_FUNCTION を明示的に外す。
--   既定の検証関数は「パスワード＝ユーザー名」を拒否するため、OBL/obl が通らなくなる。
CREATE PROFILE app_profile LIMIT
  PASSWORD_LIFE_TIME UNLIMITED
  PASSWORD_GRACE_TIME UNLIMITED
  FAILED_LOGIN_ATTEMPTS UNLIMITED
  PASSWORD_VERIFY_FUNCTION NULL;

-- SYS / SYSTEM も失効させない
ALTER PROFILE DEFAULT LIMIT
  PASSWORD_LIFE_TIME UNLIMITED
  PASSWORD_GRACE_TIME UNLIMITED;

-- 確認
SELECT directory_name, directory_path FROM dba_directories WHERE directory_name = 'DMPDIR';
SELECT profile, resource_name, limit FROM dba_profiles WHERE profile = 'APP_PROFILE';

EXIT
