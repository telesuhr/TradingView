#!/bin/bash
# ================================================================
# LME Daily Report Generator - Unix/Linux Shell Script
# Author: Claude Code
# Created: 2025-06-10
# ================================================================

echo "========================================"
echo "LME Daily Report Generator"
echo "========================================"
echo "Start Time: $(date)"
echo

# スクリプトのディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Pythonの存在確認
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.7+"
    exit 1
fi

# 必要なディレクトリ作成
mkdir -p output logs

# 設定ファイルの存在確認
if [ ! -f "config.json" ]; then
    echo "[ERROR] config.json not found. Please create configuration file."
    exit 1
fi

# 仮想環境の確認・作成
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment"
        exit 1
    fi
fi

# 仮想環境のアクティベート
echo "[INFO] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to activate virtual environment"
    exit 1
fi

# 必要なパッケージのインストール確認
echo "[INFO] Checking required packages..."
if ! pip show eikon &> /dev/null; then
    echo "[INFO] Installing required packages..."
    pip install eikon pandas numpy python-dotenv
fi

# メインスクリプトの実行
echo "[INFO] Running LME Daily Report Generator..."
python lme_daily_report.py
RESULT=$?

# 仮想環境の非アクティブ化
deactivate

# 結果表示
echo
echo "========================================"
if [ $RESULT -eq 0 ]; then
    echo "[SUCCESS] Report generation completed successfully!"
    echo "Check the 'output' directory for the generated report."
else
    echo "[ERROR] Report generation failed. Check logs for details."
fi
echo "End Time: $(date)"
echo "========================================"

exit $RESULT