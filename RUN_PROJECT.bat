@echo off
setlocal
cd /d "%~dp0"

echo ===============================================================
echo Parallel Bank Transactions ^& Fraud Detection - One Click Run
echo ===============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not on PATH.
    echo Install Python 3 and run this file again.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 (
    echo Matplotlib not found. Installing from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo [2/3] Running project...
python main.py
if errorlevel 1 (
    echo [ERROR] Project execution failed.
    pause
    exit /b 1
)

echo [3/3] Opening outputs...
if exist "outputs" start "" "%cd%\outputs"
if exist "outputs\*.png" (
    for %%F in ("outputs\*.png") do start "" "%%~fF"
)

echo.
echo Done. You can rerun this same file any time.
pause
