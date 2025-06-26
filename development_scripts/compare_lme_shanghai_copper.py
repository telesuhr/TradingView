#!/usr/bin/env python3
"""
LME銅先物 vs 上海銅先物の価格差分析
"""

import sys
import json
import eikon as ek
import pandas as pd
import numpy as np
from datetime import datetime

def load_config():
    """設定ファイル読み込み"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

def compare_lme_shanghai_copper():
    """LME vs 上海銅先物価格差分析"""
    
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
    
    print("=" * 80)
    print("LME銅先物 vs 上海銅先物 価格差分析")
    print("=" * 80)
    
    # LME銅3ヶ月先物価格取得
    lme_price = None
    lme_date = None
    try:
        lme_ric = config.get('metals_rics', {}).get('Copper', 'CMCU3')
        lme_data, lme_err = ek.get_data(lme_ric, ['CF_LAST', 'CF_DATE'])
        
        if lme_data is not None and not lme_data.empty:
            row = lme_data.iloc[0]
            lme_price = row.get('CF_LAST')
            lme_date = row.get('CF_DATE')
            
            if pd.notna(lme_price) and lme_price is not None:
                print(f"✓ LME銅3ヶ月先物 ({lme_ric}): ${lme_price:,.2f}/MT")
                print(f"  日付: {lme_date}")
            else:
                print(f"✗ LME銅価格取得失敗")
                return
        
        if lme_err:
            print(f"  LME警告: {lme_err}")
            
    except Exception as e:
        print(f"✗ LME銅価格取得エラー: {e}")
        return
    
    # 上海銅先物価格取得（第1-6限月）
    shanghai_prices = {}
    shanghai_contracts = ['SCFc1', 'SCFc2', 'SCFc3', 'SCFc4', 'SCFc5', 'SCFc6']
    
    print(f"\n上海銅先物価格取得:")
    for contract in shanghai_contracts:
        try:
            sh_data, sh_err = ek.get_data(contract, ['CF_LAST', 'CF_DATE', 'CF_VOLUME'])
            
            if sh_data is not None and not sh_data.empty:
                row = sh_data.iloc[0]
                sh_price = row.get('CF_LAST')
                sh_date = row.get('CF_DATE')
                sh_volume = row.get('CF_VOLUME')
                
                if pd.notna(sh_price) and sh_price is not None:
                    shanghai_prices[contract] = {
                        'price_cny': sh_price,
                        'date': sh_date,
                        'volume': sh_volume if pd.notna(sh_volume) else 0
                    }
                    print(f"  ✓ {contract}: {sh_price:,.0f} CNY/MT (出来高: {sh_volume:,.0f})")
                else:
                    print(f"  ✗ {contract}: 価格取得失敗")
            else:
                print(f"  ✗ {contract}: データ取得失敗")
                
            if sh_err:
                print(f"    警告: {sh_err}")
                
        except Exception as e:
            print(f"  ✗ {contract}: エラー - {e}")
    
    if not shanghai_prices:
        print("上海銅先物価格が取得できませんでした")
        return
    
    # USD/CNY為替レート取得
    usdcny_rate = None
    try:
        fx_data, fx_err = ek.get_data('CNY=', ['CF_LAST', 'CF_DATE'])
        
        if fx_data is not None and not fx_data.empty:
            row = fx_data.iloc[0]
            usdcny_rate = row.get('CF_LAST')
            fx_date = row.get('CF_DATE')
            
            if pd.notna(usdcny_rate) and usdcny_rate is not None:
                print(f"\n✓ USD/CNY為替レート: {usdcny_rate:.4f} (日付: {fx_date})")
            else:
                # フォールバック為替レート
                usdcny_rate = 7.25
                print(f"\n⚠ USD/CNY為替レート取得失敗、フォールバック値使用: {usdcny_rate:.4f}")
        
        if fx_err:
            print(f"  為替警告: {fx_err}")
            
    except Exception as e:
        usdcny_rate = 7.25
        print(f"\n⚠ USD/CNY為替レート取得エラー、フォールバック値使用: {usdcny_rate:.4f}")
    
    # 価格差分析
    print(f"\n" + "=" * 80)
    print("価格差分析結果")
    print("=" * 80)
    
    print(f"\n基準価格:")
    print(f"  LME銅3ヶ月先物: ${lme_price:,.2f}/MT")
    lme_price_cny = lme_price * usdcny_rate
    print(f"  LME銅（CNY換算）: {lme_price_cny:,.0f} CNY/MT (@{usdcny_rate:.4f})")
    
    print(f"\n🔍 価格差詳細分析:")
    
    analysis_results = []
    for contract, data in shanghai_prices.items():
        sh_price_cny = data['price_cny']
        sh_volume = data['volume']
        
        # USD換算
        sh_price_usd = sh_price_cny / usdcny_rate
        
        # 価格差計算
        diff_usd = sh_price_usd - lme_price
        diff_cny = sh_price_cny - lme_price_cny
        diff_percent = (diff_usd / lme_price) * 100
        
        # 流動性評価
        liquidity = "高" if sh_volume > 10000 else "中" if sh_volume > 1000 else "低"
        
        print(f"\n  {contract} (上海銅先物):")
        print(f"    上海価格: {sh_price_cny:,.0f} CNY/MT → ${sh_price_usd:,.2f}/MT")
        print(f"    価格差: ${diff_usd:+,.2f}/MT ({diff_cny:+,.0f} CNY/MT)")
        print(f"    価格差率: {diff_percent:+.2f}%")
        print(f"    出来高: {sh_volume:,.0f} 契約 (流動性: {liquidity})")
        
        # 価格差の市場含意
        if abs(diff_percent) < 1:
            implication = "価格収束・裁定機会なし"
        elif diff_percent > 5:
            implication = "上海プレミアム大・輸入インセンティブ高"
        elif diff_percent > 2:
            implication = "上海プレミアム・輸入インセンティブあり"
        elif diff_percent < -5:
            implication = "上海ディスカウント大・輸出インセンティブ高"
        elif diff_percent < -2:
            implication = "上海ディスカウント・輸出インセンティブあり"
        else:
            implication = "小幅差異・市場均衡"
        
        print(f"    市場含意: {implication}")
        
        analysis_results.append({
            'contract': contract,
            'sh_price_usd': sh_price_usd,
            'diff_usd': diff_usd,
            'diff_percent': diff_percent,
            'volume': sh_volume,
            'liquidity': liquidity,
            'implication': implication
        })
    
    # 加重平均価格差計算（出来高ベース）
    total_volume = sum(r['volume'] for r in analysis_results if r['volume'] > 0)
    if total_volume > 0:
        weighted_diff = sum(r['diff_usd'] * r['volume'] for r in analysis_results) / total_volume
        weighted_diff_percent = (weighted_diff / lme_price) * 100
        
        print(f"\n📊 出来高加重平均価格差:")
        print(f"  加重平均差: ${weighted_diff:+,.2f}/MT ({weighted_diff_percent:+.2f}%)")
        
        if abs(weighted_diff_percent) < 1:
            overall_assessment = "両市場は価格収束・効率的な裁定"
        elif weighted_diff_percent > 3:
            overall_assessment = "上海市場プレミアム・中国需要強or供給制約"
        elif weighted_diff_percent < -3:
            overall_assessment = "上海市場ディスカウント・中国需要弱or過剰供給"
        else:
            overall_assessment = "両市場は概ね均衡・正常な価格差"
        
        print(f"  総合評価: {overall_assessment}")
    
    # 最適な比較対象選定
    print(f"\n🎯 推奨比較対象契約:")
    high_liquidity_contracts = [r for r in analysis_results if r['volume'] > 10000]
    
    if high_liquidity_contracts:
        best_contract = max(high_liquidity_contracts, key=lambda x: x['volume'])
        print(f"  推奨: {best_contract['contract']}")
        print(f"  理由: 最高流動性 ({best_contract['volume']:,.0f} 契約)")
        print(f"  価格差: ${best_contract['diff_usd']:+,.2f}/MT ({best_contract['diff_percent']:+.2f}%)")
        print(f"  市場含意: {best_contract['implication']}")
    else:
        print("  高流動性契約が見つかりません")
    
    # 期間構造比較
    if len(analysis_results) >= 3:
        print(f"\n📈 期間構造比較:")
        print(f"  上海先物カーブ vs LMEフラット価格:")
        
        for i, result in enumerate(analysis_results[:6], 1):
            trend_arrow = "📈" if result['diff_percent'] > 1 else "📉" if result['diff_percent'] < -1 else "➡️"
            print(f"    第{i}限月: {trend_arrow} {result['diff_percent']:+.2f}%")
    
    return analysis_results, lme_price, usdcny_rate

if __name__ == "__main__":
    try:
        results, lme_price, fx_rate = compare_lme_shanghai_copper()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)