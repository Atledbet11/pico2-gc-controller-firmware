@echo off
setlocal
set MODE=%1
if "%MODE%"=="" set MODE=default
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0upload.ps1" -Mode %MODE%
endlocal
