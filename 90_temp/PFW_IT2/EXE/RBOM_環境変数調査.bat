@echo off
rem Environment variables investigation batch file
rem Get date and time for filename

set ORA_PATH=%CD%\instantclient_12c
set PATH=%ORA_PATH%;%PATH%
set ORACLE_HOME=%ORA_PATH%
set TNS_ADMIN=%ORA_PATH%
set ORACLE_SID=RBOM
set NLS_LANG=JAPANESE_JAPAN.JA16SJISTILDE

rem Get date and time (YYYYMMDD_HHMMSS format)
for /f "tokens=2 delims==" %%i in ('wmic OS Get localdatetime /value') do set dt=%%i
set DATESTAMP=%dt:~0,8%
set TIMESTAMP=%dt:~8,6%
set FILENAME=env_vars_%DATESTAMP%_%TIMESTAMP%.txt

rem Output environment variables to text file
echo ====================================== > %FILENAME%
echo Environment Variables Investigation Results >> %FILENAME%
echo Execution DateTime: %dt:~0,4%-%dt:~4,2%-%dt:~6,2% %dt:~8,2%:%dt:~10,2%:%dt:~12,2% >> %FILENAME%
echo ====================================== >> %FILENAME%
echo. >> %FILENAME%

echo [Oracle Related Environment Variables] >> %FILENAME%
echo ORA_PATH=%ORA_PATH% >> %FILENAME%
echo ORACLE_HOME=%ORACLE_HOME% >> %FILENAME%
echo TNS_ADMIN=%TNS_ADMIN% >> %FILENAME%
echo ORACLE_SID=%ORACLE_SID% >> %FILENAME%
echo NLS_LANG=%NLS_LANG% >> %FILENAME%
echo PATH=%PATH% >> %FILENAME%
echo. >> %FILENAME%

echo [System Environment Variables] >> %FILENAME%
echo COMPUTERNAME=%COMPUTERNAME% >> %FILENAME%
echo USERNAME=%USERNAME% >> %FILENAME%
echo USERDOMAIN=%USERDOMAIN% >> %FILENAME%
echo OS=%OS% >> %FILENAME%
echo PROCESSOR_ARCHITECTURE=%PROCESSOR_ARCHITECTURE% >> %FILENAME%
echo TEMP=%TEMP% >> %FILENAME%
echo TMP=%TMP% >> %FILENAME%
echo WINDIR=%WINDIR% >> %FILENAME%
echo SYSTEMROOT=%SYSTEMROOT% >> %FILENAME%
echo. >> %FILENAME%

echo [Network Configuration] >> %FILENAME%
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do echo IPv4 Address%%a >> %FILENAME%
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"Subnet Mask"') do echo Subnet Mask%%a >> %FILENAME%
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"Default Gateway"') do echo Default Gateway%%a >> %FILENAME%
echo. >> %FILENAME%

echo [Network Adapter Information] >> %FILENAME%
ipconfig /all | findstr /C:"Ethernet adapter" >> %FILENAME%
ipconfig /all | findstr /C:"Wireless LAN adapter" >> %FILENAME%
echo. >> %FILENAME%

echo [Ping Test to 172.21.0.26] >> %FILENAME%
ping -n 4 172.21.0.26 >> %FILENAME% 2>&1
echo. >> %FILENAME%

echo [Java Related Environment Variables] >> %FILENAME%
if defined JAVA_HOME echo JAVA_HOME=%JAVA_HOME% >> %FILENAME%
if defined JRE_HOME echo JRE_HOME=%JRE_HOME% >> %FILENAME%
if not defined JAVA_HOME echo JAVA_HOME=Not Set >> %FILENAME%
if not defined JRE_HOME echo JRE_HOME=Not Set >> %FILENAME%
echo. >> %FILENAME%

echo [Current Directory] >> %FILENAME%
echo CD=%CD% >> %FILENAME%
echo. >> %FILENAME%

echo Environment variables output completed: %FILENAME%