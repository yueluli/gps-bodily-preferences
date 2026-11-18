@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run setup.cmd first to prepare this folder's Python environment.
    exit /b 1
)
".venv\Scripts\python.exe" "%~dp0run_fig2_bodily.py" %*
exit /b %errorlevel%
