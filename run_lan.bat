@echo off
chcp 65001 >nul
title PaperAssistant - LAN Mode

echo ============================================
echo   PaperAssistant - 局域网部署模式
echo ============================================
echo.

REM Get LAN IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set "LAN_IP=%%a"
    set "LAN_IP=!LAN_IP: =!"
    goto :found_ip
)
:found_ip

echo   本机局域网 IP: %LAN_IP%
echo.
echo   启动服务器 (监听所有网卡)...
echo.
echo   其他设备访问地址:
echo     http://%LAN_IP%:8000
echo.
echo   本机访问: http://127.0.0.1:8000
echo.
echo   按 Ctrl+C 停止服务器
echo ============================================
echo.

setlocal enabledelayedexpansion

REM Activate conda env and run
where conda >nul 2>&1
if %errorlevel% neq 0 (
    for %%d in ("%USERPROFILE%\miniconda3" "%USERPROFILE%\anaconda3") do (
        if exist "%%d\condabin\conda.bat" ( set "PATH=%%d\condabin;%%d\Scripts;!PATH!" & goto :run )
    )
)
:run
call conda run -n paper_assistant python "%~dp0manage.py" runserver 0.0.0.0:8000
pause
