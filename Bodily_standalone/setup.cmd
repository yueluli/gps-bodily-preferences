@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3.12 -m venv .venv
    if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Setup complete. Run bodily.cmd check, then bodily.cmd run on the HKUST network.
exit /b 0
:failed
echo.
echo Setup did not finish. See README.txt for the manual Python 3.12 setup commands.
exit /b 1
