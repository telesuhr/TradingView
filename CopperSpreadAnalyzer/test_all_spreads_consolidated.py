#!/usr/bin/env python3
"""
LME Copper 全スプレッド組み合わせの前日取引データ取得テスト（統合CSV版）
全スプレッドの取引データを1つのCSVファイルにまとめて出力
"""

import eikon as ek
import pandas as pd
import json
from datetime import datetime, timedelta
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
            logging.FileHandler('logs/all_spreads_consolidated_test.log'),
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

def generate_third_wednesday_contracts(logger):
    """第3水曜日ベースの限月リストを生成（24ヶ月版）"""
    
    month_codes = {
        1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
        7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
    }
    
    contracts = []
    today = datetime.now()
    
    # 24ヶ月先まで
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
    
    logger.info(f"生成された限月: {len(contracts)}個（24ヶ月分）")
    return contracts

def generate_all_spread_combinations(contracts, logger):
    """全スプレッド組み合わせの生成（24ヶ月版、全組み合わせ）"""
    
    # 基本限月リスト（Cash + 3Month + 24ヶ月分の第3水曜限月）
    base_instruments = [
        {'code': '0', 'name': 'Cash', 'type': 'cash'},
        {'code': '3', 'name': '3Month', 'type': '3month'}
    ]
    
    # 24ヶ月分の第3水曜限月を追加
    for contract in contracts:  # 24ヶ月分全て
        base_instruments.append({
            'code': contract['contract'],
            'name': f"Third_Wed_{contract['contract']}",
            'type': 'third_wednesday'
        })
    
    logger.info(f"基本インストゥルメント: {len(base_instruments)}個（Cash + 3Month + 24ヶ月限月）")
    
    # 全組み合わせを生成（26個から2個を選ぶ組み合わせ）
    spread_combinations = []
    
    for i in range(len(base_instruments)):
        for j in range(i + 1, len(base_instruments)):
            near = base_instruments[i]
            far = base_instruments[j]
            
            # RICコード生成
            ric_code = f"CMCU{near['code']}-{far['code']}"
            
            spread_combinations.append({
                'ric': ric_code,
                'near_leg': near,
                'far_leg': far,
                'description': f"{near['name']} vs {far['name']}"
            })
    
    logger.info(f"生成されたスプレッド組み合わせ: {len(spread_combinations)}個（全組み合わせ）")
    
    # サンプル表示
    logger.info("スプレッド組み合わせのサンプル（最初の10個）:")
    for i, spread in enumerate(spread_combinations[:10]):
        logger.info(f"  {spread['ric']}: {spread['description']}")
    
    # 想定される組み合わせ数の確認
    expected_combinations = len(base_instruments) * (len(base_instruments) - 1) // 2
    logger.info(f"想定組み合わせ数: {expected_combinations}個 (26 * 25 / 2 = 325)")
    
    return spread_combinations

def test_spread_data_consolidated(spread_combinations, logger):
    """全スプレッドの取引データ一括取得（統合版）"""
    
    # 前営業日を計算
    today = datetime.now()
    previous_business_day = today - timedelta(days=1)
    while previous_business_day.weekday() >= 5:
        previous_business_day -= timedelta(days=1)
    
    # 前々営業日も計算
    start_date = previous_business_day - timedelta(days=2)
    while start_date.weekday() >= 5:
        start_date -= timedelta(days=1)
    
    date_from = start_date.strftime('%Y-%m-%d')
    date_to = previous_business_day.strftime('%Y-%m-%d')
    
    logger.info(f"取得期間: {date_from} ～ {date_to}")
    logger.info(f"テスト対象: {len(spread_combinations)}個のスプレッド")
    
    # 統合データリスト
    all_trade_data = []
    summary_data = []
    
    successful_count = 0
    failed_count = 0
    
    for i, spread in enumerate(spread_combinations):
        ric = spread['ric']
        logger.info(f"[{i+1}/{len(spread_combinations)}] {ric}: {spread['description']}")
        
        try:
            # 分単位データ取得
            df_data = ek.get_timeseries(
                ric,
                fields=['CLOSE', 'VOLUME', 'HIGH', 'LOW', 'OPEN'],
                start_date=date_from,
                end_date=date_to,
                interval='minute'
            )
            
            if df_data is not None and not df_data.empty:
                # 取引があったデータのみ抽出
                active_data = df_data[df_data['VOLUME'] > 0]
                
                if not active_data.empty:
                    # 取引データを統合リストに追加
                    for index, row in active_data.iterrows():
                        trade_record = {
                            'spread_ric': ric,
                            'near_leg': spread['near_leg']['name'],
                            'far_leg': spread['far_leg']['name'],
                            'trade_datetime': index,
                            'date': index.date(),
                            'time': index.time(),
                            'close_price': row['CLOSE'],
                            'volume': row['VOLUME'],
                            'high_price': row['HIGH'],
                            'low_price': row['LOW'],
                            'open_price': row['OPEN']
                        }
                        all_trade_data.append(trade_record)
                    
                    # サマリーデータ
                    total_volume = active_data['VOLUME'].sum()
                    trade_count = len(active_data)
                    price_min = active_data['LOW'].min()
                    price_max = active_data['HIGH'].max()
                    first_trade = active_data.index.min()
                    last_trade = active_data.index.max()
                    
                    summary_record = {
                        'spread_ric': ric,
                        'near_leg': spread['near_leg']['name'],
                        'far_leg': spread['far_leg']['name'],
                        'status': 'success_with_trades',
                        'trade_count': trade_count,
                        'total_volume': total_volume,
                        'price_min': price_min,
                        'price_max': price_max,
                        'price_range': f"{price_min:.2f} - {price_max:.2f}",
                        'first_trade': first_trade,
                        'last_trade': last_trade,
                        'date_from': date_from,
                        'date_to': date_to
                    }
                    
                    logger.info(f"  ✅ 取引データ: {trade_count}件, 総量: {total_volume}, 価格: {price_min:.2f}-{price_max:.2f}")
                    successful_count += 1
                    
                else:
                    # データはあるが取引なし
                    summary_record = {
                        'spread_ric': ric,
                        'near_leg': spread['near_leg']['name'],
                        'far_leg': spread['far_leg']['name'],
                        'status': 'success_no_trades',
                        'trade_count': 0,
                        'total_volume': 0,
                        'date_from': date_from,
                        'date_to': date_to
                    }
                    logger.info(f"  ⚪ データあり、取引なし")
            else:
                # データなし
                summary_record = {
                    'spread_ric': ric,
                    'near_leg': spread['near_leg']['name'],
                    'far_leg': spread['far_leg']['name'],
                    'status': 'no_data',
                    'trade_count': 0,
                    'total_volume': 0,
                    'date_from': date_from,
                    'date_to': date_to
                }
                logger.info(f"  ❌ データなし")
                failed_count += 1
                
        except Exception as e:
            logger.error(f"  ❌ エラー: {e}")
            summary_record = {
                'spread_ric': ric,
                'near_leg': spread['near_leg']['name'],
                'far_leg': spread['far_leg']['name'],
                'status': 'error',
                'error': str(e),
                'trade_count': 0,
                'total_volume': 0,
                'date_from': date_from,
                'date_to': date_to
            }
            failed_count += 1
        
        summary_data.append(summary_record)
        
        # API制限対策
        import time
        time.sleep(0.1)
        
        # 進捗表示（50件ごと）
        if (i + 1) % 50 == 0:
            logger.info(f"  進捗: {i+1}/{len(spread_combinations)} 完了 ({(i+1)/len(spread_combinations)*100:.1f}%)")
    
    return all_trade_data, summary_data, successful_count, failed_count

def save_consolidated_data(all_trade_data, summary_data, date_to, logger):
    """統合データの保存"""
    
    date_str = date_to
    
    # 1. 全取引データを統合CSVで保存
    if all_trade_data:
        trades_df = pd.DataFrame(all_trade_data)
        trades_df = trades_df.sort_values(['trade_datetime', 'spread_ric'])
        
        trades_file = f"output/copper_spread_trades_{date_str}.csv"
        trades_df.to_csv(trades_file, index=False, encoding='utf-8-sig')
        logger.info(f"統合取引データを保存: {trades_file} ({len(trades_df)}件)")
        
        # 日別・スプレッド別サマリー
        daily_summary = trades_df.groupby(['date', 'spread_ric']).agg({
            'volume': 'sum',
            'high_price': 'max',
            'low_price': 'min',
            'close_price': 'last',
            'trade_datetime': 'count'
        }).rename(columns={'trade_datetime': 'trade_count'}).reset_index()
        
        daily_file = f"output/copper_spread_daily_summary_{date_str}.csv"
        daily_summary.to_csv(daily_file, index=False, encoding='utf-8-sig')
        logger.info(f"日別サマリーを保存: {daily_file}")
        
    else:
        logger.warning("取引データが見つかりませんでした")
    
    # 2. スプレッド別サマリーを保存
    summary_df = pd.DataFrame(summary_data)
    summary_file = f"output/copper_spread_summary_{date_str}.csv"
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    logger.info(f"スプレッド別サマリーを保存: {summary_file}")
    
    return trades_df if all_trade_data else None, summary_df

def analyze_consolidated_results(trades_df, summary_df, successful_count, failed_count, logger):
    """統合結果の分析"""
    
    logger.info(f"\n=== 統合データ分析結果 ===")
    
    total_spreads = len(summary_df)
    success_with_trades = len(summary_df[summary_df['status'] == 'success_with_trades'])
    
    logger.info(f"総スプレッド数: {total_spreads}")
    logger.info(f"取引データあり: {success_with_trades} ({success_with_trades/total_spreads*100:.1f}%)")
    logger.info(f"成功: {successful_count}, 失敗: {failed_count}")
    
    if trades_df is not None and not trades_df.empty:
        total_trades = len(trades_df)
        total_volume = trades_df['volume'].sum()
        unique_spreads = trades_df['spread_ric'].nunique()
        
        logger.info(f"\n=== 取引データ統計 ===")
        logger.info(f"総取引件数: {total_trades:,}件")
        logger.info(f"総取引量: {total_volume:,.0f}ロット")
        logger.info(f"取引のあったスプレッド: {unique_spreads}個")
        logger.info(f"平均取引量/件: {total_volume/total_trades:.1f}ロット")
        
        # 上位スプレッド
        top_spreads = trades_df.groupby('spread_ric').agg({
            'volume': 'sum',
            'trade_datetime': 'count'
        }).rename(columns={'trade_datetime': 'trade_count'}).sort_values('volume', ascending=False)
        
        logger.info(f"\n=== 取引量上位スプレッド ===")
        for i, (ric, data) in enumerate(top_spreads.head(10).iterrows()):
            logger.info(f"{i+1:2d}. {ric:15s}: {data['volume']:6.0f}ロット ({data['trade_count']:3d}取引)")
        
        # 時間別分析
        trades_df['hour'] = trades_df['trade_datetime'].dt.hour
        hourly_volume = trades_df.groupby('hour')['volume'].sum()
        
        logger.info(f"\n=== 時間別取引量 ===")
        for hour, volume in hourly_volume.items():
            logger.info(f"{hour:2d}時: {volume:6.0f}ロット")

def main():
    """メイン実行"""
    logger = setup_logging()
    logger.info("LME Copper 全スプレッド組み合わせ取引データ取得テスト（統合版）開始")
    
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
    
    # 第3水曜限月の生成
    contracts = generate_third_wednesday_contracts(logger)
    
    # 全スプレッド組み合わせの生成
    spread_combinations = generate_all_spread_combinations(contracts, logger)
    
    # 全スプレッドの取引データ取得
    all_trade_data, summary_data, successful_count, failed_count = test_spread_data_consolidated(spread_combinations, logger)
    
    # 統合データの保存
    previous_business_day = datetime.now() - timedelta(days=1)
    while previous_business_day.weekday() >= 5:
        previous_business_day -= timedelta(days=1)
    date_str = previous_business_day.strftime('%Y-%m-%d')
    
    trades_df, summary_df = save_consolidated_data(all_trade_data, summary_data, date_str, logger)
    
    # 結果の分析
    analyze_consolidated_results(trades_df, summary_df, successful_count, failed_count, logger)
    
    logger.info("統合版スプレッド組み合わせテスト完了")

if __name__ == "__main__":
    main()