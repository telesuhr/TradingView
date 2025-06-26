#!/usr/bin/env python3
"""
CME銅先物HGc系RIC包括テスト - データ可用性と期間構造分析
"""

import sys
import json
import eikon as ek
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def load_config():
    """設定ファイル読み込み"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

def test_cme_copper_futures():
    """CME銅先物HGc系RIC包括テスト"""
    
    config = load_config()
    api_key = config.get('eikon_api_key')
    
    if not api_key:
        print("エラー: EIKON APIキーが設定されていません")
        return
    
    try:
        ek.set_app_key(api_key)
        print("EIKON API接続成功")
    except Exception as e:
        print(f"EIKON API接続エラー: {e}")
        return
    
    # CME銅先物RIC候補（第1-12限月）
    cme_copper_futures = {}
    for i in range(1, 13):  # HGc1からHGc12まで
        cme_copper_futures[f"HGc{i}"] = {
            "ric": f"HGc{i}",
            "name": f"CME銅先物第{i}限月",
            "month_num": i
        }
    
    print("=" * 80)
    print("CME銅先物HGc系RIC包括テスト - データ可用性と期間構造分析")
    print("=" * 80)
    
    results = {}
    successful_contracts = []
    failed_contracts = []
    prices_for_curve = {}
    
    for contract_code, info in cme_copper_futures.items():
        ric = info["ric"]
        name = info["name"]
        month_num = info["month_num"]
        
        print(f"\n【{name}】")
        print(f"  RIC: {ric}")
        
        try:
            # 基本データ取得テスト
            fields = ['CF_LAST', 'CF_DATE', 'CF_HIGH', 'CF_LOW', 'CF_CLOSE', 'CF_VOLUME', 'CF_OPEN']
            data, err = ek.get_data(ric, fields)
            
            if data is not None and not data.empty:
                row = data.iloc[0]
                last_price = row.get('CF_LAST')
                last_date = row.get('CF_DATE')
                high_price = row.get('CF_HIGH')
                low_price = row.get('CF_LOW')
                close_price = row.get('CF_CLOSE')
                volume = row.get('CF_VOLUME')
                open_price = row.get('CF_OPEN')
                
                if pd.notna(last_price) and last_price is not None:
                    # CME銅は通常セント/ポンドで表示、ドル/MTに変換
                    # 1ポンド = 0.453592 kg, 1MT = 1000kg
                    # セント/ポンド → ドル/MT = (価格/100) / 0.453592 * 1000
                    price_usd_per_mt = (last_price / 100) / 0.453592 * 1000
                    
                    print(f"  ✓ 最新価格: {last_price:.2f} セント/ポンド → ${price_usd_per_mt:,.2f}/MT")
                    print(f"  ✓ 日付: {last_date}")
                    
                    # 価格詳細
                    price_info = []
                    if pd.notna(open_price):
                        open_usd_mt = (open_price / 100) / 0.453592 * 1000
                        price_info.append(f"始値: {open_price:.2f}¢/lb (${open_usd_mt:,.2f}/MT)")
                    if pd.notna(high_price):
                        high_usd_mt = (high_price / 100) / 0.453592 * 1000
                        price_info.append(f"高値: {high_price:.2f}¢/lb (${high_usd_mt:,.2f}/MT)")
                    if pd.notna(low_price):
                        low_usd_mt = (low_price / 100) / 0.453592 * 1000
                        price_info.append(f"安値: {low_price:.2f}¢/lb (${low_usd_mt:,.2f}/MT)")
                    if pd.notna(close_price):
                        close_usd_mt = (close_price / 100) / 0.453592 * 1000
                        price_info.append(f"終値: {close_price:.2f}¢/lb (${close_usd_mt:,.2f}/MT)")
                    
                    if price_info:
                        print(f"  ✓ 価格詳細:")
                        for info in price_info:
                            print(f"    {info}")
                    
                    # 出来高情報
                    if pd.notna(volume) and volume is not None:
                        print(f"  ✓ 出来高: {volume:,.0f} 契約")
                        volume_liquidity = "高流動性" if volume > 10000 else "中流動性" if volume > 1000 else "低流動性"
                        print(f"  ✓ 流動性評価: {volume_liquidity}")
                    else:
                        print(f"  ⚠ 出来高: データなし")
                        volume_liquidity = "不明"
                    
                    # 時系列データテスト（過去7日）
                    try:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=7)
                        
                        ts_data = ek.get_timeseries(
                            ric,
                            fields=['CLOSE', 'VOLUME'],
                            start_date=start_date.strftime('%Y-%m-%d'),
                            end_date=end_date.strftime('%Y-%m-%d')
                        )
                        
                        if ts_data is not None and not ts_data.empty:
                            close_series = ts_data['CLOSE'].dropna()
                            volume_series = ts_data['VOLUME'].dropna()
                            
                            if len(close_series) > 0:
                                avg_price_7d = close_series.mean()
                                std_price_7d = close_series.std()
                                data_points = len(close_series)
                                
                                # セント/ポンド→ドル/MTに変換
                                avg_price_7d_usd_mt = (avg_price_7d / 100) / 0.453592 * 1000
                                std_price_7d_usd_mt = (std_price_7d / 100) / 0.453592 * 1000
                                
                                if len(volume_series) > 0:
                                    avg_volume_7d = volume_series.mean()
                                    print(f"  ✓ 7日平均価格: {avg_price_7d:.2f}¢/lb (${avg_price_7d_usd_mt:,.2f}/MT)")
                                    print(f"  ✓ 7日平均出来高: {avg_volume_7d:,.0f} 契約")
                                    print(f"  ✓ 7日標準偏差: {std_price_7d:.2f}¢/lb (${std_price_7d_usd_mt:.2f}/MT)")
                                else:
                                    avg_volume_7d = 0
                                    print(f"  ✓ 7日平均価格: {avg_price_7d:.2f}¢/lb (${avg_price_7d_usd_mt:,.2f}/MT)")
                                
                                # データ品質評価
                                if data_points >= 5 and avg_volume_7d > 1000:
                                    data_quality = "高品質"
                                elif data_points >= 3 and avg_volume_7d > 100:
                                    data_quality = "中品質"
                                else:
                                    data_quality = "低品質"
                                
                                print(f"  ✓ データ品質: {data_quality}")
                                
                                # 期間構造用の価格保存（USD/MT）
                                prices_for_curve[month_num] = price_usd_per_mt
                                
                                # 結果記録
                                results[contract_code] = {
                                    'ric': ric,
                                    'name': name,
                                    'month_num': month_num,
                                    'last_price_cents_lb': last_price,
                                    'last_price_usd_mt': price_usd_per_mt,
                                    'volume': volume if pd.notna(volume) else 0,
                                    'last_date': str(last_date),
                                    'avg_price_7d_usd_mt': avg_price_7d_usd_mt,
                                    'avg_volume_7d': avg_volume_7d,
                                    'data_points': data_points,
                                    'data_quality': data_quality,
                                    'liquidity': volume_liquidity,
                                    'status': 'success'
                                }
                                successful_contracts.append(contract_code)
                                print(f"  → 評価: 成功")
                            else:
                                print(f"  ✗ 有効な時系列データなし")
                                failed_contracts.append(contract_code)
                        else:
                            print(f"  ✗ 時系列データ取得失敗")
                            failed_contracts.append(contract_code)
                            
                    except Exception as ts_error:
                        print(f"  ✗ 時系列データエラー: {ts_error}")
                        failed_contracts.append(contract_code)
                        
                else:
                    print(f"  ✗ 有効な価格データなし")
                    failed_contracts.append(contract_code)
            else:
                print(f"  ✗ データ取得失敗")
                failed_contracts.append(contract_code)
            
            if err:
                print(f"  警告: {err}")
                
        except Exception as e:
            print(f"  ✗ RICエラー: {e}")
            failed_contracts.append(contract_code)
    
    # 結果分析
    print("\n" + "=" * 80)
    print("CME銅先物データ可用性・品質分析結果")
    print("=" * 80)
    
    if successful_contracts:
        print(f"\n✓ 有効契約: {len(successful_contracts)}/{len(cme_copper_futures)}")
        
        # 流動性別分類
        liquidity_stats = {}
        for contract in successful_contracts:
            if contract in results:
                liquidity = results[contract]['liquidity']
                if liquidity not in liquidity_stats:
                    liquidity_stats[liquidity] = []
                liquidity_stats[liquidity].append(contract)
        
        print(f"\n流動性別分類:")
        for liquidity, contracts in liquidity_stats.items():
            print(f"  {liquidity}: {len(contracts)} 契約 ({', '.join(contracts)})")
        
        # 期間構造分析
        if len(prices_for_curve) >= 3:
            print(f"\n📈 期間構造分析:")
            sorted_months = sorted(prices_for_curve.items())
            
            print(f"  期間構造カーブ（USD/MT）:")
            for month, price_usd_mt in sorted_months:
                contract_code = f"HGc{month}"
                volume = results.get(contract_code, {}).get('volume', 0)
                print(f"    第{month}限月: ${price_usd_mt:,.2f}/MT (出来高: {volume:,.0f})")
            
            # コンタンゴ/バックワーデーション判定
            if len(sorted_months) >= 2:
                near_month, near_price = sorted_months[0]
                far_month, far_price = sorted_months[-1]
                
                price_diff = far_price - near_price
                months_diff = far_month - near_month
                monthly_slope = price_diff / months_diff if months_diff > 0 else 0
                
                if price_diff > 50:  # $50/MT以上の差
                    structure = "コンタンゴ"
                    implication = "保管コスト反映・供給充足"
                elif price_diff < -50:
                    structure = "バックワーデーション"
                    implication = "現物需要逼迫・在庫不足"
                else:
                    structure = "フラット"
                    implication = "需給均衡・中立的市場"
                
                print(f"\n  期間構造判定:")
                print(f"    第{near_month}限月 vs 第{far_month}限月: {price_diff:+,.2f} USD/MT")
                print(f"    月間スロープ: {monthly_slope:+.2f} USD/MT/月")
                print(f"    構造タイプ: {structure}")
                print(f"    市場含意: {implication}")
        
        # 推奨契約ランキング
        print(f"\n🏆 推奨契約ランキング（流動性・データ品質ベース）:")
        ranking_data = []
        for contract, data in results.items():
            if data['status'] == 'success':
                # スコア計算
                volume_score = min(data.get('avg_volume_7d', 0) / 1000, 10)  # 最大10点
                quality_score = 10 if data['data_quality'] == '高品質' else 5 if data['data_quality'] == '中品質' else 1
                data_score = min(data['data_points'] * 2, 10)  # 最大10点
                
                total_score = volume_score + quality_score + data_score
                ranking_data.append((contract, data, total_score))
        
        ranking_data.sort(key=lambda x: x[2], reverse=True)
        
        for i, (contract, data, score) in enumerate(ranking_data[:6], 1):
            print(f"  {i}. {data['name']} ({contract})")
            print(f"     価格: ${data['last_price_usd_mt']:,.2f}/MT ({data['last_price_cents_lb']:.2f}¢/lb)")
            print(f"     出来高: {data.get('avg_volume_7d', 0):,.0f} 契約/日")
            print(f"     データ品質: {data['data_quality']}")
            print(f"     総合スコア: {score:.1f}")
            print()
    
    if failed_contracts:
        print(f"\n✗ 無効契約: {len(failed_contracts)}")
        for contract in failed_contracts:
            print(f"  - {contract}")
    
    print(f"\n📊 CME銅先物分析サマリー:")
    print(f"• CME銅先物は通常セント/ポンド単位")
    print(f"• USD/MT換算: (セント/ポンド ÷ 100) ÷ 0.453592 × 1000")
    print(f"• 有効契約: {len(successful_contracts)}")
    print(f"• 取得失敗: {len(failed_contracts)}")
    
    return results, successful_contracts, failed_contracts, prices_for_curve

if __name__ == "__main__":
    try:
        results, successful, failed, curve_data = test_cme_copper_futures()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)