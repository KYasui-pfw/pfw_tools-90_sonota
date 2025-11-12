@echo off
chcp 65001 >nul
echo ======================================================
echo Access データベースファイルをコピーしています...
echo ======================================================
echo.

set SOURCE1=\\172.17.81.101\schejule\cylline\Cyl_pfw_table.accdb
set SOURCE2=\\172.17.81.101\schejule\camline\EJ\EJ_DETA_SERVER\EJデータマスター.accdb
set DEST_DIR=%~dp0data

REM dataディレクトリが存在しない場合は作成
if not exist "%DEST_DIR%" (
    mkdir "%DEST_DIR%"
    echo dataディレクトリを作成しました: %DEST_DIR%
    echo.
)

REM ファイル1をコピー
echo [1/2] コピー中: %SOURCE1%
if exist "%SOURCE1%" (
    copy /Y "%SOURCE1%" "%DEST_DIR%\" >nul
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ コピー完了: Cyl_pfw_table.accdb
    ) else (
        echo   ✗ コピー失敗: Cyl_pfw_table.accdb
    )
) else (
    echo   ✗ ソースファイルが見つかりません
)
echo.

REM ファイル2をコピー
echo [2/2] コピー中: %SOURCE2%
if exist "%SOURCE2%" (
    copy /Y "%SOURCE2%" "%DEST_DIR%\" >nul
    if %ERRORLEVEL% EQU 0 (
        echo   ✓ コピー完了: EJデータマスター.accdb
    ) else (
        echo   ✗ コピー失敗: EJデータマスター.accdb
    )
) else (
    echo   ✗ ソースファイルが見つかりません
)
echo.

echo ======================================================
echo ファイルコピーが完了しました
echo ======================================================
