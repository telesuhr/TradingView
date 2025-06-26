#!/usr/bin/env python3
"""
LME Copper 全スプレッド組み合わせの前日取引データ取得テスト
Cash, 3M, 各第3水曜限月の全組み合わせを生成してデータ取得
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
            logging.FileHandler('logs/all_spreads_test.log'),
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
    """第3水曜日ベースの限月リストを生成"""
    
    # 月コードマッピング
    month_codes = {
        1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
        7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
    }
    
    contracts = []
    today = datetime.now()
    
    # 24ヶ月先まで生成
    for months_ahead in range(0, 25):
        target_date = today + timedelta(days=30 * months_ahead)
        year = target_date.year
        month = target_date.month
        
        # 第3水曜日を計算
        first_day = datetime(year, month, 1)
        first_weekday = first_day.weekday()
        
        # 第1水曜日の日付
        if first_weekday <= 2:  # 月曜(0)、火曜(1)、水曜(2)
            first_wednesday = 3 - first_weekday
        else:
            first_wednesday = 10 - first_weekday
        
        # 第3水曜日
        third_wednesday = first_wednesday + 14
        
        # 月末を超える場合は翌月の第3水曜日
        days_in_month = calendar.monthrange(year, month)[1]
        if third_wednesday > days_in_month:
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            
            # 翌月の第3水曜日を計算
            first_day_next = datetime(next_year, next_month, 1)
            first_weekday_next = first_day_next.weekday()
            
            if first_weekday_next <= 2:
                first_wednesday_next = 3 - first_weekday_next
            else:
                first_wednesday_next = 10 - first_weekday_next
            
            third_wednesday_next = first_wednesday_next + 14
            expiry_date = datetime(next_year, next_month, third_wednesday_next)
            month_code = month_codes[next_month]
            year_code = str(next_year)[-2:]
        else:
            expiry_date = datetime(year, month, third_wednesday)
            month_code = month_codes[month]
            year_code = str(year)[-2:]
        
        contract_code = f"{month_code}{year_code}"
        contracts.append({
            'contract': contract_code,
            'expiry_date': expiry_date,
            'months_ahead': months_ahead,
            'full_year': year if third_wednesday <= days_in_month else (year + 1 if month == 12 else year)
        })
    
    logger.info(f"生成された限月: {len(contracts)}個")
    for i, contract in enumerate(contracts[:12]):  # 最初の12個を表示
        logger.info(f"  {contract['contract']}: {contract['expiry_date'].strftime('%Y-%m-%d')} ({contract['months_ahead']}ヶ月先)")
    
    return contracts

def generate_spread_combinations(contracts, logger):
    """スプレッド組み合わせの生成"""
    
    # 基本限月リスト（Cash + 3M + 第3水曜限月）
    base_instruments = [
        {'code': '0', 'name': 'Cash', 'type': 'cash'},
        {'code': '3', 'name': '3Month', 'type': '3month'}
    ]
    
    # 第3水曜限月を追加
    for contract in contracts[:24]:  # 24ヶ月分
        base_instruments.append({
            'code': contract['contract'],
            'name': f"Third_Wed_{contract['contract']}",
            'type': 'third_wednesday'
        })
    
    logger.info(f"基本インストゥルメント: {len(base_instruments)}個")
    
    # 全組み合わせを生成
    spread_combinations = []
    for near, far in combinations(base_instruments, 2):
        # RICコード生成
        near_code = near['code']
        far_code = far['code']
        
        # CMCU[near]-[far]の形式
        ric_code = f"CMCU{near_code}-{far_code}"
        
        spread_combinations.append({
            'ric': ric_code,
            'near_leg': near,
            'far_leg': far,
            'description': f"{near['name']} vs {far['name']}"
        })
    
    logger.info(f"生成されたスプレッド組み合わせ: {len(spread_combinations)}個")
    
    # サンプル表示
    logger.info("スプレッド組み合わせのサンプル:")
    for i, spread in enumerate(spread_combinations[:10]):
        logger.info(f"  {spread['ric']}: {spread['description']}")
    
    return spread_combinations

def test_spread_data_bulk(spread_combinations, logger):
    """全スプレッドの前日取引データ一括取得テスト"""
    
    # 前営業日を計算
    today = datetime.now()
    previous_business_day = today - timedelta(days=1)
    while previous_business_day.weekday() >= 5:
        previous_business_day -= timedelta(days=1)
    
    # 前々営業日も計算（データ取得のため）
    start_date = previous_business_day - timedelta(days=2)
    while start_date.weekday() >= 5:
        start_date -= timedelta(days=1)
    
    date_from = start_date.strftime('%Y-%m-%d')
    date_to = previous_business_day.strftime('%Y-%m-%d')
    
    logger.info(f"取得期間: {date_from} ～ {date_to}")
    logger.info(f"テスト対象: {len(spread_combinations)}個のスプレッド")
    
    results = []
    successful_spreads = []
    failed_spreads = []
    
    # バッチサイズ（一度に処理する数）
    batch_size = 20
    
    for i in range(0, len(spread_combinations), batch_size):
        batch = spread_combinations[i:i + batch_size]
        logger.info(f"\n=== バッチ {i//batch_size + 1}: {len(batch)}個のスプレッド処理 ===")
        
        for j, spread in enumerate(batch):
            ric = spread['ric']
            logger.info(f"  [{i+j+1}/{len(spread_combinations)}] {ric}: {spread['description']}")
            
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
                        # 取引データあり
                        total_volume = active_data['VOLUME'].sum()
                        price_range = f"{active_data['LOW'].min():.2f} - {active_data['HIGH'].max():.2f}"
                        trade_times = len(active_data)
                        first_trade = active_data.index.min()
                        last_trade = active_data.index.max()
                        
                        logger.info(f"    ✅ 取引データ: {trade_times}件, 総量: {total_volume}, 価格: {price_range}")
                        
                        result = {
                            'ric': ric,
                            'description': spread['description'],
                            'status': 'success_with_trades',
                            'trade_count': trade_times,
                            'total_volume': total_volume,
                            'price_range': price_range,
                            'first_trade': first_trade,
                            'last_trade': last_trade,
                            'near_leg': spread['near_leg']['name'],
                            'far_leg': spread['far_leg']['name']
                        }
                        
                        successful_spreads.append({
                            'spread': spread,
                            'data': active_data,
                            'summary': result
                        })
                        
                    else:
                        # データはあるが取引なし
                        logger.info(f"    ⚪ データあり、取引なし")
                        result = {
                            'ric': ric,
                            'description': spread['description'],
                            'status': 'success_no_trades',
                            'near_leg': spread['near_leg']['name'],
                            'far_leg': spread['far_leg']['name']
                        }
                else:
                    # データなし
                    logger.info(f"    ❌ データなし")
                    result = {
                        'ric': ric,
                        'description': spread['description'],
                        'status': 'no_data',
                        'near_leg': spread['near_leg']['name'],
                        'far_leg': spread['far_leg']['name']
                    }
                    failed_spreads.append(spread)
                
            except Exception as e:
                logger.error(f"    ❌ エラー: {e}")
                result = {
                    'ric': ric,
                    'description': spread['description'],
                    'status': 'error',
                    'error': str(e),
                    'near_leg': spread['near_leg']['name'],
                    'far_leg': spread['far_leg']['name']
                }
                failed_spreads.append(spread)
            
            results.append(result)
            
            # API制限対策
            import time
            time.sleep(0.1)
        
        # バッチ間の待機
        if i + batch_size < len(spread_combinations):
            logger.info(f"  バッチ完了。次のバッチまで2秒待機...")
            time.sleep(2)
    
    return results, successful_spreads, failed_spreads

def analyze_results(results, successful_spreads, failed_spreads, logger):
    """結果の分析とサマリー表示"""
    
    logger.info(f"\n=== 全スプレッド取引データ取得結果サマリー ===")
    
    total_spreads = len(results)
    success_with_trades = len([r for r in results if r['status'] == 'success_with_trades'])
    success_no_trades = len([r for r in results if r['status'] == 'success_no_trades'])
    no_data = len([r for r in results if r['status'] == 'no_data'])
    errors = len([r for r in results if r['status'] == 'error'])
    
    logger.info(f"総スプレッド数: {total_spreads}")
    logger.info(f"取引データあり: {success_with_trades} ({success_with_trades/total_spreads*100:.1f}%)")
    logger.info(f"データあり・取引なし: {success_no_trades} ({success_no_trades/total_spreads*100:.1f}%)")
    logger.info(f"データなし: {no_data} ({no_data/total_spreads*100:.1f}%)")
    logger.info(f"エラー: {errors} ({errors/total_spreads*100:.1f}%)")
    
    if successful_spreads:
        logger.info(f"\n=== 取引のあったスプレッド一覧 ===")
        total_all_volume = 0
        
        # 取引量順にソート
        successful_spreads.sort(key=lambda x: x['summary']['total_volume'], reverse=True)
        
        for i, spread_data in enumerate(successful_spreads[:20]):  # 上位20個
            summary = spread_data['summary']
            logger.info(f"{i+1:2d}. {summary['ric']:12s}: {summary['total_volume']:6.0f}ロット, "
                       f"{summary['trade_count']:3d}取引, 価格{summary['price_range']}")
            total_all_volume += summary['total_volume']
        
        if len(successful_spreads) > 20:
            logger.info(f"    ... 他 {len(successful_spreads)-20}個のスプレッド")
        
        logger.info(f"\n総取引量: {total_all_volume:.0f}ロット")
        logger.info(f"平均取引量: {total_all_volume/len(successful_spreads):.1f}ロット/スプレッド")
    
    # 結果をCSVで保存
    results_df = pd.DataFrame(results)
    results_file = "output/all_spreads_test_results.csv"
    results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
    logger.info(f"\n全結果を保存: {results_file}")
    
    # 取引のあったスプレッドの詳細データを保存
    if successful_spreads:
        for spread_data in successful_spreads:
            ric = spread_data['spread']['ric']
            data = spread_data['data']
            
            # 特殊文字を除去してファイル名作成
            safe_ric = ric.replace('-', '_')
            output_file = f"output/spread_trades_{safe_ric}.csv"
            data.to_csv(output_file, encoding='utf-8-sig')
            
        logger.info(f"取引データを個別保存: {len(successful_spreads)}ファイル")
    
    return results_df

def main():
    """メイン実行"""
    logger = setup_logging()
    logger.info("LME Copper 全スプレッド組み合わせ取引データ取得テスト開始")
    
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
    
    # スプレッド組み合わせの生成
    spread_combinations = generate_spread_combinations(contracts, logger)
    
    # 全スプレッドの取引データ取得
    results, successful_spreads, failed_spreads = test_spread_data_bulk(spread_combinations, logger)
    
    # 結果の分析
    results_df = analyze_results(results, successful_spreads, failed_spreads, logger)
    
    logger.info("全スプレッド組み合わせテスト完了")

if __name__ == "__main__":
    main()