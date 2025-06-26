#!/usr/bin/env python3
"""
LME Copper スプレッド取引データ取得（ロンドン時間基準・分単位・修正版）
全スプレッド組み合わせの取引データをロンドン時間の1日単位で取得（分単位データ）
"""

import eikon as ek
import pandas as pd
import json
from datetime import datetime, timedelta
import pytz
import logging
import sys
import os
from itertools import combinations
import calendar

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/copper_spread_london_minute.log'),
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

def get_london_business_day(offset_days=1):
    """ロンドン時間基準で営業日を取得（分単位データ用API仕様対応）"""
    
    # ロンドンタイムゾーン設定
    london_tz = pytz.timezone('Europe/London')
    utc_now = datetime.now(pytz.UTC)
    london_now = utc_now.astimezone(london_tz)
    
    # 指定日数前の日付から開始
    target_date = london_now - timedelta(days=offset_days)
    
    # 営業日まで遡る（土日を除く）
    while target_date.weekday() >= 5:  # 土曜(5)、日曜(6)
        target_date -= timedelta(days=1)
    
    london_date = target_date.date()
    
    # 分単位データ取得のため、複数日期間を指定
    # APIの仕様: 目標日のデータを取得するには翌営業日まで期間指定が必要
    start_date = target_date - timedelta(days=3)  # 3営業日前から
    while start_date.weekday() >= 5:
        start_date -= timedelta(days=1)
    
    # 終了日は目標日の翌営業日に設定（APIの仕様）
    end_date = target_date + timedelta(days=1)
    while end_date.weekday() >= 5:
        end_date += timedelta(days=1)
    
    return {
        'london_date': london_date,
        'start_date': start_date.date(),
        'end_date': end_date.date(),
        'london_datetime': target_date
    }

def generate_24month_contracts(logger):
    """24ヶ月分の第3水曜限月リストを生成"""
    
    month_codes = {
        1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
        7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
    }
    
    contracts = []
    today = datetime.now()
    
    # 25ヶ月分（0-24ヶ月先）= 25個の限月
    for months_ahead in range(0, 25):
        target_date = today + timedelta(days=30 * months_ahead)
        year = target_date.year
        month = target_date.month
        
        month_code = month_codes[month]
        year_code = str(year)[-2:]
        contract_code = f"{month_code}{year_code}"
        
        contracts.append({
            'contract': contract_code,
            'months_ahead': months_ahead
        })
    
    logger.info(f"生成された限月: {len(contracts)}個（25ヶ月分: 0-24ヶ月先）")
    return contracts

def generate_all_combinations(contracts, logger):
    """全スプレッド組み合わせの生成（Cash + 3M + 25限月 = 27個から2個選ぶ）"""
    
    # 基本限月リスト
    base_instruments = [
        {'code': '0', 'name': 'Cash', 'type': 'cash'},
        {'code': '3', 'name': '3Month', 'type': '3month'}
    ]
    
    # 25ヶ月分の第3水曜限月を追加
    for contract in contracts:
        base_instruments.append({
            'code': contract['contract'],
            'name': f"Third_Wed_{contract['contract']}",
            'type': 'third_wednesday'
        })
    
    logger.info(f"基本インストゥルメント: {len(base_instruments)}個（Cash + 3Month + 25限月）")
    
    # 全組み合わせを生成
    spread_combinations = []
    
    for i in range(len(base_instruments)):
        for j in range(i + 1, len(base_instruments)):
            near = base_instruments[i]
            far = base_instruments[j]
            
            ric_code = f"CMCU{near['code']}-{far['code']}"
            
            spread_combinations.append({
                'ric': ric_code,
                'near_leg': near,
                'far_leg': far,
                'description': f"{near['name']} vs {far['name']}"
            })
    
    expected_combinations = len(base_instruments) * (len(base_instruments) - 1) // 2
    logger.info(f"生成されたスプレッド組み合わせ: {len(spread_combinations)}個 (想定: {expected_combinations}個)")
    
    return spread_combinations

def get_spread_data_london_minute(spread_combinations, london_date_info, logger, max_spreads=None):
    """ロンドン時間基準で1日のスプレッドデータを取得（分単位データ）"""
    
    # テスト数を制限（指定がない場合は全て）
    if max_spreads:
        test_combinations = spread_combinations[:max_spreads]
        logger.info(f"テスト対象を最初の{max_spreads}個に制限")
    else:
        test_combinations = spread_combinations
    
    london_date = london_date_info['london_date']
    start_date_str = london_date_info['start_date'].strftime('%Y-%m-%d')
    end_date_str = london_date_info['end_date'].strftime('%Y-%m-%d')
    
    logger.info(f"取得対象日: {london_date} (ロンドン時間)")
    logger.info(f"取得期間: {start_date_str} ～ {end_date_str} (分単位データ用)")
    logger.info(f"テスト対象: {len(test_combinations)}個のスプレッド")
    
    all_trade_data = []
    summary_data = []
    successful_count = 0
    failed_count = 0
    
    # ロンドンタイムゾーン設定
    london_tz = pytz.timezone('Europe/London')
    
    for i, spread in enumerate(test_combinations):
        ric = spread['ric']
        
        # 進捗表示
        if (i + 1) % 25 == 0 or i == 0:
            logger.info(f"[{i+1}/{len(test_combinations)}] 進捗: {(i+1)/len(test_combinations)*100:.1f}%")
        
        logger.debug(f"  {ric}: {spread['description']}")
        
        try:
            # 分単位データで取得（複数日期間指定）
            df_data = ek.get_timeseries(
                ric,
                fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
                start_date=start_date_str,
                end_date=end_date_str,
                interval='minute'
            )
            
            if df_data is not None and not df_data.empty:
                # ロンドン時間に変換
                df_data.index = pd.to_datetime(df_data.index, utc=True)
                df_data_london = df_data.copy()
                df_data_london.index = df_data_london.index.tz_convert(london_tz)
                
                # 該当日のデータのみを抽出
                daily_data = df_data_london[df_data_london.index.date == london_date]
                
                if not daily_data.empty:
                    active_data = daily_data[daily_data['VOLUME'] > 0]
                    
                    if not active_data.empty:
                        # 取引データを統合リストに追加
                        for index, row in active_data.iterrows():
                            trade_record = {
                                'spread_ric': ric,
                                'near_leg': spread['near_leg']['name'],
                                'far_leg': spread['far_leg']['name'],
                                'trade_datetime_london': index,  # ロンドン時間
                                'trade_datetime_utc': index.astimezone(pytz.UTC),  # UTC時間
                                'london_date': london_date,
                                'london_time': index.time(),
                                'close_price': row['CLOSE'],
                                'volume': row['VOLUME'],
                                'high_price': row['HIGH'],
                                'low_price': row['LOW'],
                                'open_price': row['OPEN']
                            }
                            all_trade_data.append(trade_record)
                        
                        total_volume = active_data['VOLUME'].sum()
                        trade_count = len(active_data)
                        price_min = active_data['LOW'].min()
                        price_max = active_data['HIGH'].max()
                        
                        summary_record = {
                            'spread_ric': ric,
                            'near_leg': spread['near_leg']['name'],
                            'far_leg': spread['far_leg']['name'],
                            'london_date': london_date,
                            'status': 'success_with_trades',
                            'trade_count': trade_count,
                            'total_volume': total_volume,
                            'price_min': price_min,
                            'price_max': price_max,
                            'price_range': f"{price_min:.2f} - {price_max:.2f}",
                            'first_trade_london': active_data.index.min(),
                            'last_trade_london': active_data.index.max()
                        }
                        
                        logger.info(f"  ✅ {ric}: {trade_count}取引, {total_volume}ロット, {price_min:.2f}-{price_max:.2f}")
                        successful_count += 1
                        
                    else:
                        summary_record = {
                            'spread_ric': ric,
                            'near_leg': spread['near_leg']['name'],
                            'far_leg': spread['far_leg']['name'],
                            'london_date': london_date,
                            'status': 'success_no_trades',
                            'trade_count': 0,
                            'total_volume': 0
                        }
                        logger.debug(f"  ⚪ {ric}: データあり、取引なし")
                else:
                    summary_record = {
                        'spread_ric': ric,
                        'near_leg': spread['near_leg']['name'],
                        'far_leg': spread['far_leg']['name'],
                        'london_date': london_date,
                        'status': 'no_data_for_date',
                        'trade_count': 0,
                        'total_volume': 0
                    }
                    logger.debug(f"  ❌ {ric}: 該当日データなし")
                    failed_count += 1
            else:
                summary_record = {
                    'spread_ric': ric,
                    'near_leg': spread['near_leg']['name'],
                    'far_leg': spread['far_leg']['name'],
                    'london_date': london_date,
                    'status': 'no_data',
                    'trade_count': 0,
                    'total_volume': 0
                }
                logger.debug(f"  ❌ {ric}: データなし")
                failed_count += 1
                
        except Exception as e:
            logger.debug(f"  ❌ {ric}: エラー - {e}")
            summary_record = {
                'spread_ric': ric,
                'near_leg': spread['near_leg']['name'],
                'far_leg': spread['far_leg']['name'],
                'london_date': london_date,
                'status': 'error',
                'error': str(e),
                'trade_count': 0,
                'total_volume': 0
            }
            failed_count += 1
        
        summary_data.append(summary_record)
        
        # API制限対策
        import time
        time.sleep(0.05)
    
    logger.info(f"\n処理完了: 成功 {successful_count}, 失敗 {failed_count}")
    return all_trade_data, summary_data, successful_count, failed_count, london_date

def save_london_minute_results(all_trade_data, summary_data, london_date, logger):
    """ロンドン日別分単位結果の保存"""
    
    date_str = london_date.strftime('%Y-%m-%d')
    
    # 統合取引データ
    if all_trade_data:
        trades_df = pd.DataFrame(all_trade_data)
        trades_df = trades_df.sort_values(['trade_datetime_london', 'spread_ric'])
        
        trades_file = f"output/copper_spread_trades_minute_london_{date_str}.csv"
        trades_df.to_csv(trades_file, index=False, encoding='utf-8-sig')
        logger.info(f"ロンドン日別分単位取引データを保存: {trades_file} ({len(trades_df)}件)")
    else:
        trades_df = None
        logger.warning("取引データが見つかりませんでした")
    
    # サマリーデータ
    summary_df = pd.DataFrame(summary_data)
    summary_file = f"output/copper_spread_summary_minute_london_{date_str}.csv"
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    logger.info(f"ロンドン日別分単位サマリーを保存: {summary_file}")
    
    return trades_df, summary_df

def analyze_london_minute_results(trades_df, summary_df, london_date, logger):
    """ロンドン日別分単位結果分析"""
    
    logger.info(f"\n=== ロンドン時間 {london_date} の分単位取引分析結果 ===")
    
    if trades_df is not None and not trades_df.empty:
        total_trades = len(trades_df)
        total_volume = trades_df['volume'].sum()
        unique_spreads = trades_df['spread_ric'].nunique()
        
        logger.info(f"総取引件数: {total_trades:,}件")
        logger.info(f"総取引量: {total_volume:,.0f}ロット")
        logger.info(f"取引のあったスプレッド: {unique_spreads}個")
        
        # 上位10個
        top_spreads = trades_df.groupby('spread_ric').agg({
            'volume': 'sum',
            'trade_datetime_london': 'count'
        }).rename(columns={'trade_datetime_london': 'trade_count'}).sort_values('volume', ascending=False)
        
        logger.info(f"\n=== 取引量上位スプレッド ===")
        for i, (ric, data) in enumerate(top_spreads.head(15).iterrows()):
            logger.info(f"{i+1:2d}. {ric:18s}: {data['volume']:6.0f}ロット ({data['trade_count']:3d}取引)")
        
        # ロンドン時間での時間別分析
        trades_df['london_hour'] = trades_df['trade_datetime_london'].dt.hour
        hourly_volume = trades_df.groupby('london_hour')['volume'].sum()
        
        logger.info(f"\n=== ロンドン時間別取引量 ===")
        for hour, volume in hourly_volume.items():
            logger.info(f"{hour:2d}時: {volume:6.0f}ロット")
        
        # 取引時間帯
        if not trades_df.empty:
            first_trade = trades_df['trade_datetime_london'].min()
            last_trade = trades_df['trade_datetime_london'].max()
            logger.info(f"\n取引時間帯: {first_trade.strftime('%H:%M')} ～ {last_trade.strftime('%H:%M')} (ロンドン時間)")
    
    # ステータス別統計
    status_counts = summary_df['status'].value_counts()
    logger.info(f"\n=== ステータス別統計 ===")
    for status, count in status_counts.items():
        logger.info(f"{status}: {count}個")

def main():
    """メイン実行"""
    logger = setup_logging()
    logger.info("LME Copper スプレッド取引データ取得（ロンドン時間基準・分単位・修正版）開始")
    
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
    
    # ロンドン時間基準で前営業日を取得（修正版）
    london_date_info = get_london_business_day(offset_days=1)
    logger.info(f"取得対象: ロンドン時間 {london_date_info['london_date']}")
    
    # 24ヶ月限月の生成
    contracts = generate_24month_contracts(logger)
    
    # 全組み合わせの生成
    spread_combinations = generate_all_combinations(contracts, logger)
    
    # テスト実行（最初の20個をテスト）
    max_test = min(20, len(spread_combinations))
    logger.info(f"\n最初の{max_test}個をテスト実行")
    
    all_trade_data, summary_data, successful_count, failed_count, london_date = get_spread_data_london_minute(
        spread_combinations, london_date_info, logger, max_spreads=max_test
    )
    
    # 結果保存
    trades_df, summary_df = save_london_minute_results(all_trade_data, summary_data, london_date, logger)
    
    # 結果分析
    analyze_london_minute_results(trades_df, summary_df, london_date, logger)
    
    logger.info("ロンドン時間基準分単位スプレッドデータ取得完了")

if __name__ == "__main__":
    main()