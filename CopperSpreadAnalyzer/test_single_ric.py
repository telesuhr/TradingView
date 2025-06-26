#!/usr/bin/env python3
"""
単一RICでの分足データ取得テスト
前セッションで成功したCMCU0-N25を使って分足データ取得をテスト
"""

import eikon as ek
import pandas as pd
import json
from datetime import datetime, date
import pytz
import logging
import sys
import os

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """設定ファイル読み込み"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"設定ファイル読み込みエラー: {e}")
        return None

def test_single_ric():
    """CMCU0-N25で分足データ取得テスト"""
    
    # 設定読み込み
    config = load_config()
    if not config:
        logger.error("設定ファイルの読み込みに失敗しました")
        return
    
    # EIKON API初期化
    try:
        api_key = config.get('eikon_api_key')
        if not api_key:
            logger.error("EIKON APIキーが設定されていません")
            return
        
        ek.set_app_key(api_key)
        logger.info("EIKON API初期化完了")
    except Exception as e:
        logger.error(f"EIKON API初期化エラー: {e}")
        return
    
    # テスト対象RIC（前セッションで成功したもの）
    test_ric = "CMCU0-N25"
    
    # 複数の日付パターンでテスト
    test_patterns = [
        {
            "name": "2025-06-13 to 2025-06-17 (前セッション成功パターン)",
            "start_date": "2025-06-13",
            "end_date": "2025-06-17"
        },
        {
            "name": "2025-06-13 to 2025-06-16", 
            "start_date": "2025-06-13",
            "end_date": "2025-06-16"
        },
        {
            "name": "2025-06-16 single day",
            "start_date": "2025-06-16", 
            "end_date": "2025-06-16"
        },
        {
            "name": "2025-06-17 single day",
            "start_date": "2025-06-17",
            "end_date": "2025-06-17"
        }
    ]
    
    london_tz = pytz.timezone('Europe/London')
    
    for pattern in test_patterns:
        logger.info(f"\n=== テストパターン: {pattern['name']} ===")
        logger.info(f"RIC: {test_ric}")
        logger.info(f"期間: {pattern['start_date']} ～ {pattern['end_date']}")
        
        try:
            # 分足データ取得
            df_data = ek.get_timeseries(
                test_ric,
                fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
                start_date=pattern['start_date'],
                end_date=pattern['end_date'],
                interval='minute'
            )
            
            if df_data is not None and not df_data.empty:
                logger.info(f"✅ 成功: {len(df_data)}件のデータを取得")
                
                # ロンドン時間に変換
                df_data.index = pd.to_datetime(df_data.index, utc=True)
                df_data_london = df_data.copy()
                df_data_london.index = df_data_london.index.tz_convert(london_tz)
                
                # 日付別のデータ件数を表示
                df_data_london['date'] = df_data_london.index.date
                daily_counts = df_data_london.groupby('date').size()
                
                logger.info("日付別データ件数:")
                for date_val, count in daily_counts.items():
                    logger.info(f"  {date_val}: {count}件")
                
                # 取引があったデータ（Volume > 0）を確認
                active_data = df_data_london[df_data_london['VOLUME'] > 0]
                if not active_data.empty:
                    logger.info(f"取引あり: {len(active_data)}件")
                    
                    active_daily = active_data.groupby('date').agg({
                        'VOLUME': ['count', 'sum'],
                        'CLOSE': ['min', 'max']
                    })
                    
                    logger.info("日付別取引データ:")
                    for date_val in active_daily.index:
                        count = active_daily.loc[date_val, ('VOLUME', 'count')]
                        volume = active_daily.loc[date_val, ('VOLUME', 'sum')]
                        min_price = active_daily.loc[date_val, ('CLOSE', 'min')]
                        max_price = active_daily.loc[date_val, ('CLOSE', 'max')]
                        logger.info(f"  {date_val}: {count}取引, {volume}ロット, 価格{min_price:.2f}-{max_price:.2f}")
                else:
                    logger.info("Volume > 0のデータなし")
                    
            else:
                logger.warning("❌ データなし")
                
        except Exception as e:
            logger.error(f"❌ エラー: {e}")

if __name__ == "__main__":
    test_single_ric()