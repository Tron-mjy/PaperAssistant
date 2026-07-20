@echo off
chcp 65001 >nul
set ENV_NAME=paper_assistant

echo ================================================
echo   PaperAssistant Desktop Setup
echo ================================================
echo.

REM -- Find conda --
where conda >nul 2>&1
if not errorlevel 1 goto :conda_ok
for %%d in ("%USERPROFILE%\miniconda3" "%USERPROFILE%\anaconda3") do (
    if exist "%%~d\condabin\conda.bat" ( set "PATH=%%~d\condabin;%%~d\Scripts;%PATH%" & goto :conda_ok )
)
echo [ERROR] conda not found.
pause & exit /b 1
:conda_ok

REM -- Find conda base --
for /f "tokens=*" %%i in ('conda info --base 2^>nul') do set "CONDA_BASE=%%i"
set "ENV_PYTHON=%CONDA_BASE%\envs\%ENV_NAME%\python.exe"
set "DESKTOP_DIR=%~dp0"

REM -- Step 1: Check env --
echo [1/2] Checking environment...
if not exist "%ENV_PYTHON%" (
    echo       Creating paper_assistant env...
    conda create -n %ENV_NAME% python=3.11 -y 2>nul
    if not exist "%ENV_PYTHON%" (
        conda create -n %ENV_NAME% python=3.11 -y --override-channels -c defaults 2>nul
    )
)
if not exist "%ENV_PYTHON%" (
    echo [ERROR] Failed to create environment.
    pause & exit /b 1
)
echo       OK

REM -- Step 2: Install desktop deps --
echo [2/2] Installing PySide6 + dependencies...
call "%ENV_PYTHON%" -m pip install -r "%DESKTOP_DIR%requirements.txt" --quiet
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause & exit /b 1
)
echo       OK

echo.
echo ================================================
echo   Setup complete! Start with:
echo     cd desktop
echo     conda activate %ENV_NAME%
echo     python main.py
echo ================================================
pause
