#!/usr/bin/env python3
"""
有効な時間間隔でのLME Copper Spreadデータ取得テスト
対象: Cash-Jul25 (CMCU0-N25)
有効間隔: [tick tas taq tastaq minute hour session daily weekly monthly quarterly yearly]
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
            logging.FileHandler('logs/valid_intervals_test.log'),
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

def test_valid_intervals(logger):
    """有効な時間間隔でのデータ取得テスト"""
    
    spread_ric = "CMCU0-N25"  # Cash-Jul25
    logger.info(f"有効間隔テスト対象RIC: {spread_ric}")
    
    # 前営業日を計算
    today = datetime.now()
    previous_business_day = today - timedelta(days=1)
    while previous_business_day.weekday() >= 5:
        previous_business_day -= timedelta(days=1)
    
    date_str = previous_business_day.strftime('%Y-%m-%d')
    logger.info(f"取得対象日: {date_str}")
    
    # 有効な時間間隔でテスト
    valid_intervals = ['tick', 'tas', 'taq', 'tastaq', 'minute', 'hour', 'session', 'daily']
    
    for interval in valid_intervals:
        logger.info(f"\n=== {interval}間隔データ取得テスト ===")
        try:
            df_data = ek.get_timeseries(
                spread_ric,
                fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
                start_date=date_str,
                end_date=date_str,
                interval=interval
            )
            
            if df_data is not None and not df_data.empty:
                logger.info(f"{interval}間隔データ取得成功: {len(df_data)}件")
                logger.info(f"データサンプル:\n{df_data.head(10)}")
                
                # 非ゼロ取引量のデータ
                active_data = df_data[df_data['VOLUME'] > 0]
                if not active_data.empty:
                    logger.info(f"\n実取引データ: {len(active_data)}件")
                    logger.info(f"実取引データ:\n{active_data}")
                    
                    # CSVで保存
                    output_file = f"output/spread_{interval}_active_{date_str}.csv"
                    active_data.to_csv(output_file, encoding='utf-8-sig')
                    logger.info(f"実取引データを保存: {output_file}")
                
                # 全データも保存
                output_file_all = f"output/spread_{interval}_all_{date_str}.csv"
                df_data.to_csv(output_file_all, encoding='utf-8-sig')
                logger.info(f"全データを保存: {output_file_all}")
                
            else:
                logger.warning(f"{interval}間隔データが空です")
                
        except Exception as e:
            logger.error(f"{interval}間隔データ取得エラー: {e}")
    
    # 複数日の範囲で試行（より多くのデータを取得する可能性）
    logger.info(f"\n=== 複数日範囲でのデータ取得テスト ===")
    
    # 過去1週間
    week_ago = previous_business_day - timedelta(days=7)
    logger.info(f"取得期間: {week_ago.strftime('%Y-%m-%d')} ～ {date_str}")
    
    for interval in ['minute', 'hour']:
        logger.info(f"\n--- {interval}間隔（1週間）データ取得 ---")
        try:
            df_week = ek.get_timeseries(
                spread_ric,
                fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
                start_date=week_ago.strftime('%Y-%m-%d'),
                end_date=date_str,
                interval=interval
            )
            
            if df_week is not None and not df_week.empty:
                logger.info(f"{interval}間隔（1週間）データ取得成功: {len(df_week)}件")
                
                # 取引のあった時間のみ抽出
                active_week = df_week[df_week['VOLUME'] > 0]
                logger.info(f"取引のあった時間: {len(active_week)}件")
                
                if not active_week.empty:
                    logger.info(f"取引データサンプル:\n{active_week.head(10)}")
                    
                    # 日別の取引サマリー
                    active_week['date'] = active_week.index.date
                    daily_summary = active_week.groupby('date').agg({
                        'VOLUME': 'sum',
                        'HIGH': 'max',
                        'LOW': 'min',
                        'CLOSE': 'last'
                    })
                    logger.info(f"\n日別取引サマリー:\n{daily_summary}")
                    
                    # CSVで保存
                    output_file = f"output/spread_{interval}_week_active.csv"
                    active_week.to_csv(output_file, encoding='utf-8-sig')
                    logger.info(f"週間取引データを保存: {output_file}")
                
            else:
                logger.warning(f"{interval}間隔（1週間）データが空です")
                
        except Exception as e:
            logger.error(f"{interval}間隔（1週間）データ取得エラー: {e}")

def test_alternative_trade_data(logger):
    """代替的な取引データ取得方法のテスト"""
    
    spread_ric = "CMCU0-N25"
    logger.info(f"\n=== 代替取引データ取得方法テスト ===")
    
    # 前営業日
    today = datetime.now()
    previous_business_day = today - timedelta(days=1)
    while previous_business_day.weekday() >= 5:
        previous_business_day -= timedelta(days=1)
    date_str = previous_business_day.strftime('%Y-%m-%d')
    
    # テスト1: より詳細なフィールドでの取引データ取得
    logger.info("\n--- 詳細フィールドでの取引データ取得 ---")
    
    trade_fields = [
        # 取引価格・数量
        'TR.TRADEPRICE', 'TR.TRADEVOLUME', 'TR.TRADETIME', 'TR.TRADEDATE',
        # ビッド・アスク
        'TR.BIDPRICE', 'TR.ASKPRICE', 'TR.BIDSZ', 'TR.ASKSZ',
        # 追加取引情報
        'TR.OPENPRICE', 'TR.HIGHPRICE', 'TR.LOWPRICE', 'TR.CLOSEPRICE'
    ]
    
    try:
        df_detailed, err = ek.get_data(
            spread_ric, 
            trade_fields,
            {'SDate': date_str, 'EDate': date_str}
        )
        
        if err:
            logger.warning(f"詳細取引データ警告: {err}")
        
        if df_detailed is not None and not df_detailed.empty:
            logger.info(f"詳細取引データ取得成功: {len(df_detailed)}件")
            logger.info(f"取得データ:\n{df_detailed}")
            
            output_file = f"output/spread_detailed_fields_{date_str}.csv"
            df_detailed.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"詳細取引データを保存: {output_file}")
        else:
            logger.warning("詳細取引データが空です")
            
    except Exception as e:
        logger.error(f"詳細取引データ取得エラー: {e}")
    
    # テスト2: 取引履歴用フィールドでの取得
    logger.info("\n--- 取引履歴フィールドでの取得 ---")
    
    history_fields = [
        'TR.PriceHigh', 'TR.PriceLow', 'TR.PriceOpen', 'TR.PriceClose',
        'TR.Volume', 'TR.TotalReturn', 'TR.PriceCloseDate'
    ]
    
    try:
        df_history, err = ek.get_data(
            spread_ric, 
            history_fields,
            {'SDate': date_str, 'EDate': date_str}
        )
        
        if err:
            logger.warning(f"取引履歴データ警告: {err}")
        
        if df_history is not None and not df_history.empty:
            logger.info(f"取引履歴データ取得成功: {len(df_history)}件")
            logger.info(f"取得データ:\n{df_history}")
            
            output_file = f"output/spread_history_{date_str}.csv"
            df_history.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"取引履歴データを保存: {output_file}")
        else:
            logger.warning("取引履歴データが空です")
            
    except Exception as e:
        logger.error(f"取引履歴データ取得エラー: {e}")

def main():
    """メイン実行"""
    logger = setup_logging()
    logger.info("有効間隔でのLME Copper Spreadデータ取得テスト開始")
    
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
    
    # 有効間隔でのデータ取得テスト
    test_valid_intervals(logger)
    
    # 代替取引データ取得テスト
    test_alternative_trade_data(logger)
    
    logger.info("有効間隔データ取得テスト完了")

if __name__ == "__main__":
    main()