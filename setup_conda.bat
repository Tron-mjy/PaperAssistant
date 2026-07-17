@echo off
chcp 65001 >nul
set ENV_NAME=paper_assistant

echo.
echo ================================================
echo   PaperAssistant - Conda Env Setup
echo ================================================
echo.

REM ---- Find conda ----
where conda >nul 2>&1
if not errorlevel 1 goto :conda_ok

for %%d in ("%USERPROFILE%\miniconda3" "%USERPROFILE%\anaconda3" "%USERPROFILE%\miniforge3" "%ProgramData%\miniconda3" "%ProgramData%\anaconda3") do (
    if exist "%%~d\condabin\conda.bat" (
        set "PATH=%%~d\condabin;%%~d\Scripts;%PATH%"
        goto :conda_ok
    )
)
echo [ERROR] conda not found.
echo   Install Miniconda: https://docs.conda.io/en/latest/miniconda.html
pause
exit /b 1

:conda_ok

REM ---- Find conda base path ----
for /f "tokens=*" %%i in ('conda info --base 2^>nul') do set "CONDA_BASE=%%i"
set "ENV_PYTHON=%CONDA_BASE%\envs\%ENV_NAME%\python.exe"

REM ---- Step 1: create env ----
echo [1/3] Environment: %ENV_NAME% (Python 3.11)
if exist "%ENV_PYTHON%" (
    echo       Already exists, skip creation.
    goto :step2
)

echo       Creating (this may take a few minutes)...
conda create -n %ENV_NAME% python=3.11 -y 2>nul
if exist "%ENV_PYTHON%" goto :step2

REM Retry with default channels (mirror fallback)
echo       Mirror failed, retrying with default channels...
conda create -n %ENV_NAME% python=3.11 -y --override-channels -c defaults 2>nul
if exist "%ENV_PYTHON%" goto :step2

echo [ERROR] Failed to create environment.
echo   Check your network, or create manually:
echo     conda create -n %ENV_NAME% python=3.11 -y
pause
exit /b 1

:step2
REM ---- Step 2: install deps ----
echo.
echo [2/3] Installing Python packages...
call "%ENV_PYTHON%" -m pip install -r "%~dp0requirements.txt" --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed. Check network.
    pause
    exit /b 1
)
echo       OK

REM ---- Step 3: migrate db ----
echo.
echo [3/3] Initializing database...
call "%ENV_PYTHON%" "%~dp0manage.py" migrate
if errorlevel 1 (
    echo [ERROR] Migration failed.
    pause
    exit /b 1
)
echo       OK

echo.
echo ================================================
echo   Setup complete!
echo.
echo   1. Edit .env - set OPENAI_API_KEY
echo   2. Start: double-click run_lan.bat
echo      or:    conda activate %ENV_NAME%
echo             python manage.py runserver
echo   3. Open  http://127.0.0.1:8000
echo ================================================
pause
