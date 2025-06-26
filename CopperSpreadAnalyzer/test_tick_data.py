#!/usr/bin/env python3
"""
LME Copper Spread ティックデータ（全取引明細）取得テスト
対象: Cash-Jul25 (CMCU0-N25)
"""

import eikon as ek
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
import sys
import os

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/tick_data_test.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_config():
    """設定ファイル読み込み"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return None

def test_tick_data_methods(logger):
    """ティックデータ取得方法のテスト"""
    
    spread_ric = "CMCU0-N25"  # Cash-Jul25
    logger.info(f"ティックデータ取得テスト対象RIC: {spread_ric}")
    
    # 前営業日を計算
    today = datetime.now()
    previous_business_day = today - timedelta(days=1)
    while previous_business_day.weekday() >= 5:
        previous_business_day -= timedelta(days=1)
    
    date_str = previous_business_day.strftime('%Y-%m-%d')
    logger.info(f"取得対象日: {date_str}")
    
    # テスト1: 分足データ取得
    logger.info("=== テスト1: 分足データ取得 ===")
    intervals = ['1min', '5min', '10min', '30min', '1h']
    
    for interval in intervals:
        logger.info(f"\n--- {interval}足データ取得 ---")
        try:
            df_interval = ek.get_timeseries(
                spread_ric,
                fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
                start_date=date_str,
                end_date=date_str,
                interval=interval
            )
            
            if df_interval is not None and not df_interval.empty:
                logger.info(f"{interval}足データ取得成功: {len(df_interval)}件")
                logger.info(f"データサンプル:\n{df_interval.head()}")
                
                # CSVで保存
                output_file = f"output/spread_tick_{interval}_{date_str}.csv"
                df_interval.to_csv(output_file, encoding='utf-8-sig')
                logger.info(f"データを保存: {output_file}")
            else:
                logger.warning(f"{interval}足データが空です")
                
        except Exception as e:
            logger.error(f"{interval}足データ取得エラー: {e}")
    
    # テスト2: ティック（tick）データ直接取得
    logger.info("\n=== テスト2: ティック（tick）データ直接取得 ===")
    try:
        df_tick = ek.get_timeseries(
            spread_ric,
            fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW'],
            start_date=date_str,
            end_date=date_str,
            interval='tick'  # ティック間隔指定
        )
        
        if df_tick is not None and not df_tick.empty:
            logger.info(f"ティックデータ取得成功: {len(df_tick)}件")
            logger.info(f"データサンプル:\n{df_tick.head(10)}")
            
            # 詳細分析
            logger.info("\n--- ティックデータ詳細分析 ---")
            logger.info(f"データ期間: {df_tick.index.min()} ～ {df_tick.index.max()}")
            logger.info(f"総取引量: {df_tick['VOLUME'].sum()}")
            logger.info(f"価格レンジ: {df_tick['LOW'].min()} ～ {df_tick['HIGH'].max()}")
            
            # ティック毎の価格変動
            df_tick['price_change'] = df_tick['CLOSE'].diff()
            logger.info(f"最大価格変動: {df_tick['price_change'].max()}")
            logger.info(f"最小価格変動: {df_tick['price_change'].min()}")
            
            # CSVで保存
            output_file = f"output/spread_tick_data_{date_str}.csv"
            df_tick.to_csv(output_file, encoding='utf-8-sig')
            logger.info(f"ティックデータを保存: {output_file}")
            
            # 取引時間分析
            df_tick['hour'] = df_tick.index.hour
            hourly_volume = df_tick.groupby('hour')['VOLUME'].sum()
            logger.info(f"\n時間別取引量:\n{hourly_volume}")
            
        else:
            logger.warning("ティックデータが空です")
            
    except Exception as e:
        logger.error(f"ティックデータ取得エラー: {e}")
    
    # テスト3: より細かい時間間隔での取得
    logger.info("\n=== テスト3: 超細かい時間間隔での取得 ===")
    fine_intervals = ['tas', 'taq', 'minute', 'second']  # 可能な最小間隔
    
    for interval in fine_intervals:
        logger.info(f"\n--- {interval}間隔データ取得 ---")
        try:
            df_fine = ek.get_timeseries(
                spread_ric,
                start_date=date_str,
                end_date=date_str,
                interval=interval
            )
            
            if df_fine is not None and not df_fine.empty:
                logger.info(f"{interval}間隔データ取得成功: {len(df_fine)}件")
                logger.info(f"データサンプル:\n{df_fine.head()}")
                
                output_file = f"output/spread_{interval}_{date_str}.csv"
                df_fine.to_csv(output_file, encoding='utf-8-sig')
                logger.info(f"データを保存: {output_file}")
            else:
                logger.warning(f"{interval}間隔データが空です")
                
        except Exception as e:
            logger.error(f"{interval}間隔データ取得エラー: {e}")
    
    # テスト4: 取引明細用専用フィールドでの取得
    logger.info("\n=== テスト4: 取引明細専用フィールドでの取得 ===")
    
    # より詳細な取引情報を取得するフィールド
    detailed_fields = [
        'TR.TRADEPRICE', 'TR.TRADEVOLUME', 'TR.TRADETIME', 'TR.TRADEDATE',
        'TR.BIDSZ', 'TR.ASKSZ', 'TR.BIDPRICE', 'TR.ASKPRICE'
    ]
    
    try:
        logger.info(f"詳細取引フィールド: {detailed_fields}")
        
        # 日付範囲を指定して取引データを取得
        df_trades, err = ek.get_data(
            spread_ric, 
            detailed_fields,
            {'SDate': date_str, 'EDate': date_str}
        )
        
        if err:
            logger.warning(f"詳細取引データ取得警告: {err}")
        
        if df_trades is not None and not df_trades.empty:
            logger.info(f"詳細取引データ取得成功: {len(df_trades)}件")
            logger.info(f"データサンプル:\n{df_trades}")
            
            output_file = f"output/spread_detailed_trades_{date_str}.csv"
            df_trades.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"詳細取引データを保存: {output_file}")
        else:
            logger.warning("詳細取引データが空です")
            
    except Exception as e:
        logger.error(f"詳細取引データ取得エラー: {e}")
    
    # テスト5: 時系列データをより細かい時間で取得
    logger.info("\n=== テスト5: 時間を分割してより詳細な取得 ===")
    try:
        # 前日を数時間に分割して取得
        start_time = previous_business_day.replace(hour=8, minute=0, second=0)  # 8:00から開始
        end_time = previous_business_day.replace(hour=17, minute=0, second=0)   # 17:00まで
        
        logger.info(f"取引時間範囲: {start_time} ～ {end_time}")
        
        df_detailed_time = ek.get_timeseries(
            spread_ric,
            fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
            start_date=start_time,
            end_date=end_time,
            interval='1min'
        )
        
        if df_detailed_time is not None and not df_detailed_time.empty:
            logger.info(f"詳細時間データ取得成功: {len(df_detailed_time)}件")
            logger.info(f"データサンプル:\n{df_detailed_time.head(10)}")
            logger.info(f"データサンプル（末尾）:\n{df_detailed_time.tail(10)}")
            
            output_file = f"output/spread_detailed_timeline_{date_str}.csv"
            df_detailed_time.to_csv(output_file, encoding='utf-8-sig')
            logger.info(f"詳細時間データを保存: {output_file}")
            
            # 非ゼロ取引量のデータのみ抽出
            active_trades = df_detailed_time[df_detailed_time['VOLUME'] > 0]
            if not active_trades.empty:
                logger.info(f"\n実取引データ: {len(active_trades)}件")
                logger.info(f"実取引データサンプル:\n{active_trades}")
                
                output_file_active = f"output/spread_active_trades_{date_str}.csv"
                active_trades.to_csv(output_file_active, encoding='utf-8-sig')
                logger.info(f"実取引データを保存: {output_file_active}")
            else:
                logger.warning("実取引データが見つかりません")
        else:
            logger.warning("詳細時間データが空です")
            
    except Exception as e:
        logger.error(f"詳細時間データ取得エラー: {e}")

def main():
    """メイン実行"""
    logger = setup_logging()
    logger.info("LME Copper Spreadティックデータ取得テスト開始")
    
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
    
    # ティックデータ取得テスト実行
    test_tick_data_methods(logger)
    
    logger.info("ティックデータ取得テスト完了")

if __name__ == "__main__":
    main()