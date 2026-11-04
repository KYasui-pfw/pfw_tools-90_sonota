@echo off
rem Task Scheduler entry point. Pass-through args to ps1 (e.g. run.bat -DryRun)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0clean_empty_folders.ps1" %*
exit /b %ERRORLEVEL%
