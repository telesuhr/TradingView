@echo off
REM ================================================================
REM LME Daily Report Generator - Windows Batch Script
REM Author: Claude Code
REM Created: 2025-06-10
REM ================================================================

echo ========================================
echo LME Daily Report Generator
echo ========================================
echo Start Time: %date% %time%
echo.

REM 現在のディレクトリを保存
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Pythonの存在確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.7+
    pause
    exit /b 1
)

REM 必要なディレクトリ作成
if not exist "output" mkdir output
if not exist "logs" mkdir logs

REM 設定ファイルの存在確認
if not exist "config.json" (
    echo [ERROR] config.json not found. Please create configuration file.
    pause
    exit /b 1
)

REM 仮想環境の確認・作成
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM 仮想環境のアクティベート
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM 必要なパッケージのインストール確認
echo [INFO] Checking required packages...
pip show eikon >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages...
    pip install eikon pandas numpy python-dotenv
)

REM メインスクリプトの実行
echo [INFO] Running LME Daily Report Generator...
python lme_daily_report.py
set RESULT=%errorlevel%

REM 仮想環境の非アクティブ化
call venv\Scripts\deactivate.bat

REM 結果表示
echo.
echo ========================================
if %RESULT% equ 0 (
    echo [SUCCESS] Report generation completed successfully!
    echo Check the 'output' directory for the generated report.
) else (
    echo [ERROR] Report generation failed. Check logs for details.
)
echo End Time: %date% %time%
echo ========================================

REM 結果に応じて終了
if %RESULT% neq 0 (
    pause
    exit /b %RESULT%
)

REM 成功時は5秒後に自動終了（タスクスケジューラー対応）
timeout /t 5 /nobreak >nul
exit /b 0