#!/usr/bin/env python3
"""
LME Copper Spread (Cash-Jul25) 分単位データの履歴取得範囲テスト
どこまで遡ってデータを取得できるかを検証
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
            logging.FileHandler('logs/historical_range_test.log'),
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

def test_historical_data_range(logger):
    """履歴データ取得範囲のテスト"""
    
    spread_ric = "CMCU0-N25"  # Cash-Jul25
    logger.info(f"履歴範囲テスト対象RIC: {spread_ric}")
    
    today = datetime.now()
    
    # テスト期間のリスト（日数）
    test_periods = [
        1,    # 1日前
        3,    # 3日前
        7,    # 1週間前
        14,   # 2週間前
        30,   # 1ヶ月前
        60,   # 2ヶ月前
        90,   # 3ヶ月前
        180,  # 6ヶ月前
        365   # 1年前
    ]
    
    results = []
    
    for days_back in test_periods:
        start_date = today - timedelta(days=days_back)
        end_date = today - timedelta(days=1)  # 前日まで
        
        logger.info(f"\n=== {days_back}日前からのデータ取得テスト ===")
        logger.info(f"期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}")
        
        try:
            # 分単位データ取得
            df_minute = ek.get_timeseries(
                spread_ric,
                fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                interval='minute'
            )
            
            if df_minute is not None and not df_minute.empty:
                # 取引があったデータのみ抽出
                active_data = df_minute[df_minute['VOLUME'] > 0]
                
                logger.info(f"分単位データ取得成功: 全{len(df_minute)}件, 実取引{len(active_data)}件")
                
                if not active_data.empty:
                    # データの期間と統計
                    first_trade = active_data.index.min()
                    last_trade = active_data.index.max()
                    total_volume = active_data['VOLUME'].sum()
                    price_range = f"{active_data['LOW'].min():.2f} - {active_data['HIGH'].max():.2f}"
                    
                    logger.info(f"実取引期間: {first_trade} ～ {last_trade}")
                    logger.info(f"総取引量: {total_volume}")
                    logger.info(f"価格レンジ: {price_range}")
                    
                    # 日別サマリー
                    active_data['date'] = active_data.index.date
                    daily_summary = active_data.groupby('date').agg({
                        'VOLUME': 'sum',
                        'HIGH': 'max',
                        'LOW': 'min',
                        'CLOSE': 'last'
                    })
                    
                    trading_days = len(daily_summary)
                    logger.info(f"取引日数: {trading_days}日")
                    
                    if trading_days <= 10:  # 少ない場合は詳細表示
                        logger.info(f"日別取引サマリー:\n{daily_summary}")
                    else:
                        logger.info(f"日別取引サマリー（最初と最後の5日）:")
                        logger.info(f"最初の5日:\n{daily_summary.head()}")
                        logger.info(f"最後の5日:\n{daily_summary.tail()}")
                    
                    # 結果記録
                    result = {
                        'days_back': days_back,
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d'),
                        'success': True,
                        'total_records': len(df_minute),
                        'active_records': len(active_data),
                        'trading_days': trading_days,
                        'total_volume': total_volume,
                        'first_trade': first_trade,
                        'last_trade': last_trade,
                        'price_range': price_range
                    }
                    
                    # CSVで保存（サンプル）
                    if days_back in [7, 30, 90]:  # 特定期間のみファイル保存
                        output_file = f"output/spread_minute_{days_back}days_back.csv"
                        active_data.to_csv(output_file, encoding='utf-8-sig')
                        logger.info(f"サンプルデータを保存: {output_file}")
                
                else:
                    logger.warning("実取引データが見つかりません")
                    result = {
                        'days_back': days_back,
                        'start_date': start_date.strftime('%Y-%m-%d'),
                        'end_date': end_date.strftime('%Y-%m-%d'),
                        'success': True,
                        'total_records': len(df_minute),
                        'active_records': 0,
                        'trading_days': 0,
                        'total_volume': 0,
                        'message': 'データあるが取引なし'
                    }
            
            else:
                logger.warning("データが取得できませんでした")
                result = {
                    'days_back': days_back,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'success': False,
                    'message': 'データなし'
                }
                
        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            result = {
                'days_back': days_back,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'success': False,
                'error': str(e)
            }
        
        results.append(result)
        
        # API制限を避けるため少し待機
        import time
        time.sleep(1)
    
    # 結果サマリー
    logger.info(f"\n=== 履歴データ取得範囲テスト結果サマリー ===")
    
    successful_periods = [r for r in results if r.get('success', False)]
    failed_periods = [r for r in results if not r.get('success', False)]
    
    logger.info(f"成功した期間: {len(successful_periods)}/{len(test_periods)}")
    
    if successful_periods:
        logger.info("\n成功した期間の詳細:")
        for result in successful_periods:
            if result.get('active_records', 0) > 0:
                logger.info(f"  {result['days_back']}日前: {result['active_records']}取引, "
                          f"{result['trading_days']}日間, 総量{result['total_volume']}")
            else:
                logger.info(f"  {result['days_back']}日前: データあり、取引なし")
    
    if failed_periods:
        logger.info(f"\n失敗した期間: {len(failed_periods)}件")
        for result in failed_periods:
            logger.info(f"  {result['days_back']}日前: {result.get('message', result.get('error', '不明'))}")
    
    # 最適な取得期間の推定
    active_periods = [r for r in successful_periods if r.get('active_records', 0) > 0]
    if active_periods:
        max_successful_days = max([r['days_back'] for r in active_periods])
        logger.info(f"\n取引データが確認できた最大期間: {max_successful_days}日前まで")
        
        # 推奨期間
        recommended_days = min(30, max_successful_days)  # 最大30日、または取得可能な最大日数
        logger.info(f"推奨取得期間: {recommended_days}日前まで")
    
    # 結果をCSVで保存
    results_df = pd.DataFrame(results)
    results_file = "output/historical_range_test_results.csv"
    results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
    logger.info(f"\nテスト結果を保存: {results_file}")
    
    return results

def test_specific_recent_dates(logger):
    """最近の特定日付での詳細テスト"""
    
    spread_ric = "CMCU0-N25"
    logger.info(f"\n=== 最近の特定日付での詳細テスト ===")
    
    today = datetime.now()
    
    # 過去10日間の各日をテスト
    for i in range(1, 11):
        test_date = today - timedelta(days=i)
        
        # 土日をスキップ
        if test_date.weekday() >= 5:
            continue
            
        date_str = test_date.strftime('%Y-%m-%d')
        logger.info(f"\n--- {date_str} ({test_date.strftime('%A')}) のデータテスト ---")
        
        try:
            df_day = ek.get_timeseries(
                spread_ric,
                fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
                start_date=date_str,
                end_date=date_str,
                interval='minute'
            )
            
            if df_day is not None and not df_day.empty:
                active_day = df_day[df_day['VOLUME'] > 0]
                
                if not active_day.empty:
                    logger.info(f"  取引データ: {len(active_day)}件")
                    logger.info(f"  取引時間: {active_day.index.min().strftime('%H:%M')} - {active_day.index.max().strftime('%H:%M')}")
                    logger.info(f"  総取引量: {active_day['VOLUME'].sum()}")
                    logger.info(f"  価格レンジ: {active_day['LOW'].min():.2f} - {active_day['HIGH'].max():.2f}")
                else:
                    logger.info("  取引なし")
            else:
                logger.info("  データなし")
                
        except Exception as e:
            logger.error(f"  エラー: {e}")

def main():
    """メイン実行"""
    logger = setup_logging()
    logger.info("LME Copper Spread履歴データ範囲テスト開始")
    
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
    
    # 履歴データ範囲テスト
    results = test_historical_data_range(logger)
    
    # 最近の日付での詳細テスト
    test_specific_recent_dates(logger)
    
    logger.info("履歴データ範囲テスト完了")

if __name__ == "__main__":
    main()