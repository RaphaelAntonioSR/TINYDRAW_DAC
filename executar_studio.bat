@echo off
setlocal
cd /d "%~dp0"
py tinydraw_studio.py
set "RESULTADO=%ERRORLEVEL%"
if not "%RESULTADO%"=="0" pause
exit /b %RESULTADO%
