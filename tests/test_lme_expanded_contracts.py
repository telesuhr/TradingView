#!/usr/bin/env python3
"""
LME拡張契約テスト - 第1〜第6限月データ取得確認
"""

import sys
import json
import eikon as ek
import pandas as pd
from datetime import datetime

def load_config():
    """設定ファイル読み込み"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

def test_lme_expanded_contracts():
    """LME拡張契約テスト"""
    
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
    
    # config.jsonからLME銅契約を読み込み
    exchange_curves = config.get('exchange_curves', {})
    copper_curves = exchange_curves.get('copper', {})
    lme_config = copper_curves.get('lme', {})
    
    if not lme_config:
        print("エラー: LME銅契約設定が見つかりません")
        return
    
    print("=" * 80)
    print("LME拡張契約テスト - 第1〜第6限月データ取得確認")
    print("=" * 80)
    
    print(f"\n【LME設定確認】")
    print(f"取引所名: {lme_config.get('exchange_name', 'N/A')}")
    print(f"通貨: {lme_config.get('currency', 'N/A')}")
    print(f"単位: {lme_config.get('unit', 'N/A')}")
    
    contracts = lme_config.get('contracts', {})
    print(f"設定契約数: {len(contracts)}")
    
    # 結果格納
    results = {}
    successful_contracts = []
    failed_contracts = []
    prices_by_month = {}
    
    # 各契約をテスト
    for contract_key, contract_info in contracts.items():
        ric = contract_info.get('ric')
        name = contract_info.get('name')
        maturity_months = contract_info.get('maturity_months')
        liquidity_tier = contract_info.get('liquidity_tier', 'unknown')
        
        print(f"\n【{name}】")
        print(f"  RIC: {ric}")
        print(f"  満期月数: {maturity_months}")
        print(f"  流動性階層: {liquidity_tier}")
        
        try:
            # 基本データ取得
            fields = ['CF_LAST', 'CF_DATE', 'CF_HIGH', 'CF_LOW', 'CF_CLOSE', 'CF_VOLUME']
            data, err = ek.get_data(ric, fields)
            
            if data is not None and not data.empty:
                row = data.iloc[0]
                last_price = row.get('CF_LAST')
                last_date = row.get('CF_DATE')
                high_price = row.get('CF_HIGH')
                low_price = row.get('CF_LOW')
                close_price = row.get('CF_CLOSE')
                volume = row.get('CF_VOLUME')
                
                if pd.notna(last_price) and last_price is not None:
                    print(f"  ✓ 最新価格: ${last_price:,.2f}/MT")
                    print(f"  ✓ 日付: {last_date}")
                    
                    # 価格詳細
                    price_details = []
                    if pd.notna(high_price):
                        price_details.append(f"高値: ${high_price:,.2f}")
                    if pd.notna(low_price):
                        price_details.append(f"安値: ${low_price:,.2f}")
                    if pd.notna(close_price):
                        price_details.append(f"終値: ${close_price:,.2f}")
                    
                    if price_details:
                        print(f"  ✓ 価格詳細: {', '.join(price_details)}")
                    
                    # 出来高
                    if pd.notna(volume) and volume is not None:
                        print(f"  ✓ 出来高: {volume:,.0f} 契約")
                    
                    # 結果記録
                    results[contract_key] = {
                        'ric': ric,
                        'name': name,
                        'maturity_months': maturity_months,
                        'last_price': last_price,
                        'last_date': str(last_date),
                        'volume': volume if pd.notna(volume) else 0,
                        'liquidity_tier': liquidity_tier,
                        'status': 'success'
                    }
                    
                    prices_by_month[maturity_months] = last_price
                    successful_contracts.append(contract_key)
                    print(f"  → 評価: 成功")
                    
                else:
                    print(f"  ✗ 有効な価格データなし")
                    failed_contracts.append(contract_key)
            else:
                print(f"  ✗ データ取得失敗")
                failed_contracts.append(contract_key)
            
            if err:
                print(f"  警告: {err}")
                
        except Exception as e:
            print(f"  ✗ RICエラー: {e}")
            failed_contracts.append(contract_key)
    
    # 結果分析
    print("\n" + "=" * 80)
    print("LME拡張契約テスト結果")
    print("=" * 80)
    
    print(f"\n✓ 有効契約: {len(successful_contracts)}/{len(contracts)}")
    if successful_contracts:
        print(f"  成功: {', '.join(successful_contracts)}")
    
    if failed_contracts:
        print(f"\n✗ 無効契約: {len(failed_contracts)}")
        print(f"  失敗: {', '.join(failed_contracts)}")
    
    # 期間構造分析
    if len(prices_by_month) >= 3:
        print(f"\n📈 期間構造分析:")
        sorted_months = sorted(prices_by_month.items())
        
        print(f"  価格カーブ:")
        for month, price in sorted_months:
            contract_key = next((k for k, v in contracts.items() if v.get('maturity_months') == month), 'N/A')
            volume = results.get(contract_key, {}).get('volume', 0)
            print(f"    {month}ヶ月: ${price:,.2f}/MT (出来高: {volume:,.0f})")
        
        # コンタンゴ/バックワーデーション判定
        if len(sorted_months) >= 2:
            near_month, near_price = sorted_months[0]
            far_month, far_price = sorted_months[-1]
            
            price_diff = far_price - near_price
            months_diff = far_month - near_month
            monthly_slope = price_diff / months_diff if months_diff > 0 else 0
            
            if price_diff > 50:
                structure = "コンタンゴ"
            elif price_diff < -50:
                structure = "バックワーデーション"
            else:
                structure = "フラット"
            
            print(f"\n  期間構造判定:")
            print(f"    {near_month}ヶ月 vs {far_month}ヶ月: {price_diff:+,.2f} USD/MT")
            print(f"    月間スロープ: {monthly_slope:+.2f} USD/MT/月")
            print(f"    構造タイプ: {structure}")
    
    # 第1〜第6限月の表示確認
    print(f"\n📊 第1〜第6限月表示確認:")
    target_months = [0, 1, 2, 3, 4, 5, 6]  # cash含む
    display_ready = True
    
    for month_num in target_months:
        contract_found = False
        for contract_key, contract_info in contracts.items():
            if contract_info.get('maturity_months') == month_num:
                result = results.get(contract_key, {})
                if result.get('status') == 'success':
                    if month_num == 0:
                        print(f"  現金決済: ✓ ${result['last_price']:,.2f}/MT")
                    else:
                        print(f"  第{month_num}限月: ✓ ${result['last_price']:,.2f}/MT")
                    contract_found = True
                    break
        
        if not contract_found:
            if month_num == 0:
                print(f"  現金決済: ✗ データなし")
            else:
                print(f"  第{month_num}限月: ✗ データなし")
            display_ready = False
    
    print(f"\n💡 他取引所との比較準備状況:")
    if display_ready:
        print("  ✓ LMEは第1〜第6限月のデータが揃っており、他取引所と同じ形式で比較可能")
    else:
        print("  ✗ 一部データが欠損しているため、完全な比較ができません")
    
    return results, successful_contracts, failed_contracts, prices_by_month

if __name__ == "__main__":
    try:
        results, successful, failed, prices = test_lme_expanded_contracts()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)