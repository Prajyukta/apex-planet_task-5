@echo off
setlocal
cd /d "%~dp0.."
if not exist logs mkdir logs
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
python scripts\automated_pipeline.py --notify >> logs\pipeline_%DATE:~-4%%DATE:~4,2%%DATE:~7,2%.log 2>&1
if errorlevel 1 (
  echo Pipeline failed. See logs for details.
  exit /b 1
)
echo Pipeline completed successfully.
endlocal
