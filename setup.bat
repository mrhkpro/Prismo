@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
title Quasar - RAG Widget SaaS
cd /d "%~dp0"

echo ================================================================
echo   Quasar - RAG Widget SaaS
echo   One-click Windows setup and local launcher
echo ================================================================
echo.

set "PY_CMD="
where python >nul 2>nul
if not errorlevel 1 set "PY_CMD=python"
if not defined PY_CMD (
    where py >nul 2>nul
    if not errorlevel 1 set "PY_CMD=py"
)
if not defined PY_CMD (
    echo ERROR: Python 3.10+ was not found.
    echo Install Python from https://python.org and enable PATH support.
    pause
    exit /b 1
)

"%PY_CMD%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python 3.10 or newer is required.
    pause
    exit /b 1
)

echo [1/4] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    "%PY_CMD%" -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo       Existing .venv found.
)

set "VENV_PY=%cd%\.venv\Scripts\python.exe"

"%VENV_PY%" -m pip --version >nul 2>nul
if errorlevel 1 (
    echo ERROR: pip is not available inside the virtual environment.
    echo Trying to restore pip with ensurepip...
    "%VENV_PY%" -m ensurepip --upgrade >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Could not restore pip.
        pause
        exit /b 1
    )
)

rem Clear stale local DNS information when Windows allows it. This does not change
rem network settings and is safe to skip if the command is unavailable.
ipconfig /flushdns >nul 2>nul

echo [2/4] Installing Python dependencies...
echo.
echo   The installer will try multiple HTTPS package indexes.
echo   This helps when files.pythonhosted.org cannot be resolved on the current network.
echo.

rem Users may override the default order for their network:
rem   set QUASAR_PIP_INDEX_URL=https://your-mirror.example/simple
if defined QUASAR_PIP_INDEX_URL (
    echo   Trying custom index: %QUASAR_PIP_INDEX_URL%
    call :install_from_index "%QUASAR_PIP_INDEX_URL%"
    if not errorlevel 1 goto deps_ok
)

echo   Trying official PyPI...
call :install_from_index "https://pypi.org/simple"
if not errorlevel 1 goto deps_ok

echo.
echo   Official PyPI was not reachable. Trying TUNA mirror...
call :install_from_index "https://pypi.tuna.tsinghua.edu.cn/simple"
if not errorlevel 1 goto deps_ok

echo.
echo   TUNA mirror was not reachable. Trying USTC mirror...
call :install_from_index "https://pypi.mirrors.ustc.edu.cn/simple"
if not errorlevel 1 goto deps_ok

echo.
echo   USTC mirror was not reachable. Trying Aliyun mirror...
call :install_from_index "https://mirrors.aliyun.com/pypi/simple"
if not errorlevel 1 goto deps_ok

echo.
echo ERROR: Failed to install dependencies from all configured package indexes.
echo.
echo The original NameResolutionError means Windows could not resolve the package server.
echo This is a network/DNS problem, not a PyJWT package error.
echo.
echo Troubleshooting:
echo   1. Run: ipconfig /flushdns
echo   2. Check that normal HTTPS websites open in the same network.
echo   3. Check proxy/VPN/firewall/DNS settings if your network requires them.
echo   4. You can set a custom mirror before running setup.bat:
echo      set QUASAR_PIP_INDEX_URL=https://your-mirror.example/simple
pause
exit /b 1

:deps_ok

echo.
echo       Dependencies installed successfully.

echo [3/4] Preparing local data and environment...
if not exist "data" mkdir data
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo       Created .env from .env.example.
)

echo [4/4] Opening Quasar setup...
"%VENV_PY%" app\setup_bootstrap.py
if errorlevel 1 (
    echo ERROR: Local setup page failed to start.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   Quasar is running at http://127.0.0.1:8000/
echo.
echo   Default admin username: admin
echo   Default admin password: Admin@12345
echo.
echo   Set provider settings in your local .env before using AI calls.
echo   Never commit .env or real API keys to Git.
echo ================================================================
echo.
pause
endlocal
exit /b 0

:install_from_index
"%VENV_PY%" -m pip install -r requirements.txt --index-url "%~1" --retries 2 --timeout 30 --disable-pip-version-check --prefer-binary
exit /b %errorlevel%
