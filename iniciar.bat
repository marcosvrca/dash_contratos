@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 servidor.py
  goto fim
)
where python >nul 2>&1
if %errorlevel%==0 (
  python servidor.py
  goto fim
)
echo Python 3 nao encontrado. Instale Python 3 e execute este arquivo de novo.
:fim
if not %errorlevel%==0 pause
