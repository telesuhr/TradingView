#!/usr/bin/env python3
"""
LME Copper スプレッド取引データ一括取得（過去1ヶ月分）
段階的実行用スクリプト
"""

import sys
import os
from datetime import datetime, timedelta
import argparse

# メインスクリプトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from copper_spread_jst_minute import (
    setup_logging, load_config, generate_24month_contracts, 
    generate_all_combinations, get_specific_date,
    get_spread_data_minute, save_minute_results,
    get_business_days_range
)
import eikon as ek

def run_single_date(target_date_str, logger):
    """単一日付のデータ取得"""
    logger.info(f"\n{'='*60}")
    logger.info(f"データ取得開始: {target_date_str}")
    logger.info(f"{'='*60}")
    
    try:
        # 日付情報の作成
        date_info = get_specific_date(target_date_str)
        
        # 24ヶ月限月の生成
        contracts = generate_24month_contracts(logger)
        
        # 全組み合わせの生成
        spread_combinations = generate_all_combinations(contracts, logger)
        
        # データ取得
        all_trade_data, summary_data, successful_count, failed_count, processed_date = get_spread_data_minute(
            spread_combinations, date_info, logger, max_spreads=None
        )
        
        # 結果保存
        trades_df, summary_df = save_minute_results(all_trade_data, summary_data, processed_date, logger)
        
        logger.info(f"✅ {target_date_str}: 取引あり {successful_count}個, データなし {failed_count}個")
        return True, successful_count, failed_count
        
    except Exception as e:
        logger.error(f"❌ {target_date_str}: エラー - {e}")
        return False, 0, 0

def run_date_range(start_date_str, end_date_str, logger):
    """指定期間のデータ取得"""
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    
    # 期間内の営業日を取得
    business_days = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:  # 土日を除く
            business_days.append(current_date)
        current_date += timedelta(days=1)
    
    logger.info(f"対象期間: {start_date_str} ～ {end_date_str}")
    logger.info(f"営業日数: {len(business_days)}日")
    
    total_success = 0
    total_failed = 0
    processed_count = 0
    
    for target_date in business_days:
        success, successful_count, failed_count = run_single_date(
            target_date.strftime('%Y-%m-%d'), logger
        )
        
        if success:
            total_success += successful_count
            total_failed += failed_count
            processed_count += 1
        
        # API制限対策
        import time
        time.sleep(2)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"期間処理完了: {start_date_str} ～ {end_date_str}")
    logger.info(f"{'='*60}")
    logger.info(f"処理済み日数: {processed_count}/{len(business_days)}")
    logger.info(f"総取引あり: {total_success}")
    logger.info(f"総データなし: {total_failed}")

def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description='LME Copper Spread Historical Data Collector')
    parser.add_argument('--date', type=str, help='単一日付 (YYYY-MM-DD)')
    parser.add_argument('--start', type=str, help='開始日 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='終了日 (YYYY-MM-DD)')
    parser.add_argument('--recent', type=int, default=7, help='直近N営業日 (デフォルト: 7)')
    
    args = parser.parse_args()
    
    # ログ設定
    logger = setup_logging()
    logger.info("LME Copper スプレッド一括取得ツール開始")
    
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
    
    # 実行モード判定
    if args.date:
        # 単一日付実行
        success, successful_count, failed_count = run_single_date(args.date, logger)
        
    elif args.start and args.end:
        # 期間指定実行
        run_date_range(args.start, args.end, logger)
        
    else:
        # 直近N営業日実行
        business_days = get_business_days_range(args.recent)
        start_date = business_days[0].strftime('%Y-%m-%d')
        end_date = business_days[-1].strftime('%Y-%m-%d')
        
        logger.info(f"直近{args.recent}営業日のデータ取得")
        run_date_range(start_date, end_date, logger)
    
    logger.info("一括取得ツール完了")

if __name__ == "__main__":
    main()