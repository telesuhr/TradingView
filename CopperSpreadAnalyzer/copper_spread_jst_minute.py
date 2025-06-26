#!/usr/bin/env python3
"""
LME Copper スプレッド取引データ取得（日本時間基準・分単位・シンプル版）
全スプレッド組み合わせの取引データを日本時間の1日単位で取得（分単位データ）
"""

import eikon as ek
import pandas as pd
import json
from datetime import datetime, timedelta, date
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
            logging.FileHandler('logs/copper_spread_jst_minute.log'),
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

def get_business_day(offset_days=1):
    """前営業日を取得（日本時間ベース・シンプル版）"""
    
    today = datetime.now()
    target_date = today - timedelta(days=offset_days)
    
    # 営業日まで遡る（土日を除く）
    while target_date.weekday() >= 5:  # 土曜(5)、日曜(6)
        target_date -= timedelta(days=1)
    
    target_date_only = target_date.date()
    
    # API仕様対応: 分足データ取得のための日付範囲設定
    start_date = target_date - timedelta(days=3)  # 3日前から
    while start_date.weekday() >= 5:
        start_date -= timedelta(days=1)
    
    # 終了日は目標日の翌営業日
    end_date = target_date + timedelta(days=1)
    while end_date.weekday() >= 5:
        end_date += timedelta(days=1)
    
    return {
        'target_date': target_date_only,
        'start_date': start_date.date(),
        'end_date': end_date.date(),
        'target_datetime': target_date
    }

def get_specific_date(target_date_str):
    """指定日のデータ取得用日付設定"""
    
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    target_date_only = target_date.date()
    
    # API仕様対応: 分足データ取得のための日付範囲設定
    start_date = target_date - timedelta(days=3)  # 3日前から
    while start_date.weekday() >= 5:
        start_date -= timedelta(days=1)
    
    # 終了日は目標日の翌営業日
    end_date = target_date + timedelta(days=1)
    while end_date.weekday() >= 5:
        end_date += timedelta(days=1)
    
    return {
        'target_date': target_date_only,
        'start_date': start_date.date(),
        'end_date': end_date.date(),
        'target_datetime': target_date
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
            'name': contract['contract'],  # Third_Wedプレフィックスを削除
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

def get_previous_close_price(ric, target_date, logger):
    """前日終値を取得（過去1週間まで遡って検索）"""
    try:
        from datetime import timedelta
        
        # 過去1週間まで遡って前日終値を検索
        for days_back in range(1, 8):
            prev_date = target_date - timedelta(days=days_back)
            
            # 土日をスキップ
            if prev_date.weekday() >= 5:
                continue
            
            # 前日の日次データを取得
            prev_date_str = prev_date.strftime('%Y-%m-%d')
            
            try:
                df_prev = ek.get_timeseries(
                    ric,
                    fields=['CLOSE'],
                    start_date=prev_date_str,
                    end_date=prev_date_str,
                    interval='daily'
                )
                
                if df_prev is not None and not df_prev.empty:
                    close_price = df_prev['CLOSE'].iloc[-1]
                    # pandas NAの値をチェック
                    if pd.isna(close_price):
                        logger.debug(f"前日終値がNA {ric} ({prev_date_str})")
                        continue
                    logger.debug(f"前日終値取得成功 {ric}: {close_price} ({prev_date_str})")
                    return close_price
                    
            except Exception as e:
                logger.debug(f"前日終値取得試行失敗 {ric} ({prev_date_str}): {e}")
                continue
        
        # 1週間遡っても見つからない場合
        logger.info(f"前日終値が見つかりません {ric}: 過去1週間にデータなし")
        return None
            
    except Exception as e:
        logger.warning(f"前日終値取得エラー {ric}: {e}")
        return None

def get_spread_data_minute(spread_combinations, date_info, logger, max_spreads=None):
    """分単位スプレッドデータを取得（シンプル版）"""
    
    # テスト数を制限（指定がない場合は全て）
    if max_spreads:
        test_combinations = spread_combinations[:max_spreads]
        logger.info(f"テスト対象を最初の{max_spreads}個に制限")
    else:
        test_combinations = spread_combinations
    
    target_date = date_info['target_date']
    start_date_str = date_info['start_date'].strftime('%Y-%m-%d')
    end_date_str = date_info['end_date'].strftime('%Y-%m-%d')
    
    logger.info(f"取得対象日: {target_date}")
    logger.info(f"取得期間: {start_date_str} ～ {end_date_str} (分単位データ用)")
    logger.info(f"テスト対象: {len(test_combinations)}個のスプレッド")
    
    all_trade_data = []
    summary_data = []
    successful_count = 0
    failed_count = 0
    
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
                # 日付でフィルタリング（タイムゾーン変換なしのシンプル処理）
                df_data.index = pd.to_datetime(df_data.index)
                daily_data = df_data[df_data.index.date == target_date]
                
                if not daily_data.empty:
                    active_data = daily_data[daily_data['VOLUME'] > 0]
                    
                    if not active_data.empty:
                        # 取引データを統合リストに追加
                        for index, row in active_data.iterrows():
                            trade_record = {
                                'spread_ric': ric,
                                'near_leg': spread['near_leg']['name'],
                                'far_leg': spread['far_leg']['name'],
                                'trade_datetime': index,
                                'trade_date': target_date,
                                'trade_time': index.time(),
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
                        
                        # 前日終値を取得
                        prev_close = get_previous_close_price(ric, target_date, logger)
                        
                        # 最終取引価格を取得（最後の取引のCLOSE価格）
                        final_close_price = active_data.iloc[-1]['CLOSE']
                        
                        # NA値を適切に処理
                        prev_close_value = None if pd.isna(prev_close) else prev_close
                        final_close_value = None if pd.isna(final_close_price) else final_close_price
                        
                        summary_record = {
                            'spread_ric': ric,
                            'near_leg': spread['near_leg']['name'],
                            'far_leg': spread['far_leg']['name'],
                            'trade_date': target_date,
                            'status': 'success_with_trades',
                            'trade_count': trade_count,
                            'total_volume': total_volume,
                            'price_min': price_min,
                            'price_max': price_max,
                            'price_range': f"{price_min:.2f} - {price_max:.2f}",
                            'first_trade': active_data.index.min(),
                            'last_trade': active_data.index.max(),
                            'previous_close': prev_close_value,
                            'final_closing_price': final_close_value
                        }
                        
                        logger.info(f"  ✅ {ric}: {trade_count}取引, {total_volume}ロット, {price_min:.2f}-{price_max:.2f}")
                        successful_count += 1
                        
                    else:
                        summary_record = {
                            'spread_ric': ric,
                            'near_leg': spread['near_leg']['name'],
                            'far_leg': spread['far_leg']['name'],
                            'trade_date': target_date,
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
                        'trade_date': target_date,
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
                    'trade_date': target_date,
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
                'trade_date': target_date,
                'status': 'error',
                'error': str(e),
                'trade_count': 0,
                'total_volume': 0
            }
            failed_count += 1
        
        # 取引があったスプレッドのみサマリーに追加
        if summary_record['status'] == 'success_with_trades':
            summary_data.append(summary_record)
        
        # API制限対策
        import time
        time.sleep(0.05)
    
    logger.info(f"\n処理完了: 成功 {successful_count}, 失敗 {failed_count}")
    return all_trade_data, summary_data, successful_count, failed_count, target_date

def save_minute_results(all_trade_data, summary_data, target_date, logger):
    """分単位結果の保存（シンプル版）"""
    
    date_str = target_date.strftime('%Y-%m-%d')
    
    # 統合取引データ
    if all_trade_data:
        trades_df = pd.DataFrame(all_trade_data)
        trades_df = trades_df.sort_values(['trade_datetime', 'spread_ric'])
        
        trades_file = f"output/copper_spread_trades_minute_jst_{date_str}.csv"
        trades_df.to_csv(trades_file, index=False, encoding='utf-8-sig')
        logger.info(f"分単位取引データを保存: {trades_file} ({len(trades_df)}件)")
    else:
        trades_df = None
        logger.warning("取引データが見つかりませんでした")
    
    # サマリーデータ
    summary_df = pd.DataFrame(summary_data)
    summary_file = f"output/copper_spread_summary_minute_jst_{date_str}.csv"
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    logger.info(f"分単位サマリーを保存: {summary_file}")
    
    return trades_df, summary_df

def analyze_minute_results(trades_df, summary_df, target_date, logger):
    """分単位結果分析（シンプル版）"""
    
    logger.info(f"\n=== {target_date} の分単位取引分析結果 ===")
    
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
            'trade_datetime': 'count'
        }).rename(columns={'trade_datetime': 'trade_count'}).sort_values('volume', ascending=False)
        
        logger.info(f"\n=== 取引量上位スプレッド ===")
        for i, (ric, data) in enumerate(top_spreads.head(15).iterrows()):
            logger.info(f"{i+1:2d}. {ric:18s}: {data['volume']:6.0f}ロット ({data['trade_count']:3d}取引)")
        
        # 時間別分析
        trades_df['hour'] = trades_df['trade_datetime'].dt.hour
        hourly_volume = trades_df.groupby('hour')['volume'].sum()
        
        logger.info(f"\n=== 時間別取引量 ===")
        for hour, volume in hourly_volume.items():
            logger.info(f"{hour:2d}時: {volume:6.0f}ロット")
        
        # 取引時間帯
        if not trades_df.empty:
            first_trade = trades_df['trade_datetime'].min()
            last_trade = trades_df['trade_datetime'].max()
            logger.info(f"\n取引時間帯: {first_trade.strftime('%H:%M')} ～ {last_trade.strftime('%H:%M')}")
    
    # ステータス別統計
    status_counts = summary_df['status'].value_counts()
    logger.info(f"\n=== ステータス別統計 ===")
    for status, count in status_counts.items():
        logger.info(f"{status}: {count}個")

def get_business_days_range(days_back=30):
    """過去の営業日リストを生成"""
    business_days = []
    current_date = datetime.now()
    days_found = 0
    check_date = current_date
    
    while days_found < days_back:
        check_date -= timedelta(days=1)
        # 土日を除外
        if check_date.weekday() < 5:  # 月曜=0, 金曜=4
            business_days.append(check_date.date())
            days_found += 1
    
    # 古い順にソート
    business_days.reverse()
    return business_days

def run_historical_batch(target_days=30, logger=None):
    """過去の営業日分をバッチ処理で取得"""
    if not logger:
        logger = setup_logging()
    
    logger.info(f"過去{target_days}営業日分のデータ取得を開始")
    
    # 営業日リスト生成
    business_days = get_business_days_range(target_days)
    logger.info(f"対象営業日: {len(business_days)}日 ({business_days[0]} ～ {business_days[-1]})")
    
    # 24ヶ月限月の生成
    contracts = generate_24month_contracts(logger)
    
    # 全組み合わせの生成
    spread_combinations = generate_all_combinations(contracts, logger)
    
    total_success = 0
    total_failed = 0
    processed_dates = []
    
    for i, target_date in enumerate(business_days):
        logger.info(f"\n{'='*60}")
        logger.info(f"処理中 [{i+1}/{len(business_days)}]: {target_date}")
        logger.info(f"{'='*60}")
        
        try:
            # 日付情報の作成
            date_info = get_specific_date(target_date.strftime('%Y-%m-%d'))
            
            # データ取得
            all_trade_data, summary_data, successful_count, failed_count, processed_date = get_spread_data_minute(
                spread_combinations, date_info, logger, max_spreads=None
            )
            
            # 結果保存
            trades_df, summary_df = save_minute_results(all_trade_data, summary_data, processed_date, logger)
            
            # 統計更新
            total_success += successful_count
            total_failed += failed_count
            processed_dates.append(target_date)
            
            logger.info(f"✅ {target_date}: 成功 {successful_count}, 失敗 {failed_count}")
            
            # API制限対策
            import time
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ {target_date}: エラー - {e}")
            continue
    
    # 最終統計
    logger.info(f"\n{'='*60}")
    logger.info(f"バッチ処理完了")
    logger.info(f"{'='*60}")
    logger.info(f"処理済み日数: {len(processed_dates)}/{len(business_days)}")
    logger.info(f"総成功: {total_success}")
    logger.info(f"総失敗: {total_failed}")
    logger.info(f"処理期間: {processed_dates[0] if processed_dates else 'N/A'} ～ {processed_dates[-1] if processed_dates else 'N/A'}")
    
    return processed_dates

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
    import re
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
    import re
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

def run_single_date_interactive(target_date_str, logger):
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

def run_date_range_interactive(start_date_str, end_date_str, logger):
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
        success, successful_count, failed_count = run_single_date_interactive(
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
        success, successful_count, failed_count = run_single_date_interactive(date_str, logger)
        
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