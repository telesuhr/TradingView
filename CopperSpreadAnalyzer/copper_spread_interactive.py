#!/usr/bin/env python3
"""
LME Copper スプレッド取引データ取得（対話型版）
ユーザーに取得対象日を質問して実行
"""

import sys
import os
from datetime import datetime, timedelta
import re

# メインスクリプトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from copper_spread_jst_minute import (
    setup_logging, load_config, generate_24month_contracts, 
    generate_all_combinations, get_specific_date,
    get_spread_data_minute, save_minute_results,
    get_business_days_range, run_historical_batch
)
import eikon as ek

def get_user_choice():
    """ユーザーの実行モード選択"""
    print("\n" + "="*50)
    print("LME銅スプレッドデータ取得システム")
    print("="*50)
    print("実行モードを選択してください:")
    print("1. 単一日付を指定")
    print("2. 期間を指定")
    print("3. 直近N営業日")
    print("4. 過去1ヶ月分（自動）")
    print("="*50)
    
    while True:
        choice = input("選択 (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return int(choice)
        print("1-4の数字を入力してください")

def get_single_date():
    """単一日付入力"""
    while True:
        date_str = input("取得日を入力 (YYYY-MM-DD形式): ").strip()
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                return date_str
            except ValueError:
                print("有効な日付を入力してください")
        else:
            print("YYYY-MM-DD形式で入力してください")

def get_date_range():
    """期間指定入力"""
    print("取得期間を指定してください")
    start_date = input("開始日 (YYYY-MM-DD): ").strip()
    end_date = input("終了日 (YYYY-MM-DD): ").strip()
    
    # 簡単な形式チェック
    for date_str in [start_date, end_date]:
        if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            print(f"無効な日付形式: {date_str}")
            return None, None
    
    return start_date, end_date

def get_recent_days():
    """直近営業日数入力"""
    while True:
        try:
            days = int(input("直近何営業日のデータを取得しますか？ (デフォルト: 7): ").strip() or "7")
            if days > 0:
                return days
            print("正の整数を入力してください")
        except ValueError:
            print("数字を入力してください")

def run_single_date(target_date_str, logger):
    """単一日付のデータ取得"""
    from run_historical_batch import run_single_date as batch_single
    return batch_single(target_date_str, logger)

def run_date_range_interactive(start_date_str, end_date_str, logger):
    """指定期間のデータ取得"""
    from run_historical_batch import run_date_range
    run_date_range(start_date_str, end_date_str, logger)

def main():
    """メイン実行（対話型）"""
    logger = setup_logging()
    logger.info("LME Copper スプレッド取引データ取得（対話型版）開始")
    
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
    
    # ユーザー選択
    choice = get_user_choice()
    
    if choice == 1:
        # 単一日付
        date_str = get_single_date()
        print(f"\n{date_str}のデータ取得を開始します...")
        success, successful_count, failed_count = run_single_date(date_str, logger)
        
        if success:
            print(f"✅ 完了: 取引あり {successful_count}個, データなし {failed_count}個")
        else:
            print("❌ エラーが発生しました")
    
    elif choice == 2:
        # 期間指定
        start_date, end_date = get_date_range()
        if start_date and end_date:
            print(f"\n{start_date} ～ {end_date}のデータ取得を開始します...")
            run_date_range_interactive(start_date, end_date, logger)
        else:
            print("無効な期間が指定されました")
    
    elif choice == 3:
        # 直近N営業日
        days = get_recent_days()
        print(f"\n直近{days}営業日のデータ取得を開始します...")
        business_days = get_business_days_range(days)
        start_date = business_days[0].strftime('%Y-%m-%d')
        end_date = business_days[-1].strftime('%Y-%m-%d')
        run_date_range_interactive(start_date, end_date, logger)
    
    elif choice == 4:
        # 過去1ヶ月分（自動）
        print(f"\n過去1ヶ月分（30営業日）のデータ取得を開始します...")
        processed_dates = run_historical_batch(target_days=30, logger=logger)
        print(f"✅ 完了: {len(processed_dates)}日分のデータを取得しました")
    
    logger.info("対話型データ取得完了")

if __name__ == "__main__":
    main()