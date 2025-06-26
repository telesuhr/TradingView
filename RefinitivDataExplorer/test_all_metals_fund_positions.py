#!/usr/bin/env python3
"""
Test All Metals Fund Position Data
全金属のファンドポジションデータテスト

Author: Claude Code  
Created: 2025-06-26
"""

import eikon as ek
import pandas as pd
import json
import time

def test_all_metals_fund_positions():
    """全金属のファンドポジションデータテスト"""
    
    # 設定読み込み
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # EIKON API初期化
    ek.set_app_key(config["eikon_api_key"])
    
    print("📊 全LME金属ファンドポジションテスト")
    print("=" * 60)
    print("既知パターン: LME-INFUS-CA (Short), LME-INFUL-CA (Long)")
    print("=" * 60)
    
    # 推定される金属別ファンドポジションRICパターン
    metals = ["CA", "AL", "ZN", "PB", "NI", "SN"]  # Copper, Aluminum, Zinc, Lead, Nickel, Tin
    metal_names = ["Copper", "Aluminium", "Zinc", "Lead", "Nickel", "Tin"]
    
    fund_position_data = {}
    
    print("\n1. 全金属ファンドポジション探索:")
    print("-" * 50)
    
    for i, (metal_code, metal_name) in enumerate(zip(metals, metal_names)):
        print(f"\n🔍 {metal_name} ({metal_code}):")
        
        # 推定RICパターン
        long_ric = f"LME-INFUL-{metal_code}"
        short_ric = f"LME-INFUS-{metal_code}"
        
        metal_data = {}
        
        # ロングポジションテスト
        try:
            long_data, long_err = ek.get_data(long_ric, ['CF_LAST', 'CF_NAME', 'CF_DATE'])
            if long_data is not None and not long_data.empty:
                row = long_data.iloc[0]
                long_value = row.get('CF_LAST')
                long_name = row.get('CF_NAME', 'N/A')
                long_date = row.get('CF_DATE', 'N/A')
                
                if pd.notna(long_value) and long_value is not None:
                    metal_data['long'] = {
                        'value': float(long_value),
                        'name': long_name,
                        'date': str(long_date),
                        'ric': long_ric
                    }
                    print(f"  ✅ ロング: {long_value:,.2f} ({long_name})")
                else:
                    print(f"  ❌ ロング: データ空")
            else:
                print(f"  ❌ ロング: アクセス失敗 ({long_ric})")
                
            if long_err:
                print(f"    警告: {long_err}")
                
        except Exception as e:
            print(f"  ❌ ロング: エラー - {e}")
        
        time.sleep(0.3)
        
        # ショートポジションテスト
        try:
            short_data, short_err = ek.get_data(short_ric, ['CF_LAST', 'CF_NAME', 'CF_DATE'])
            if short_data is not None and not short_data.empty:
                row = short_data.iloc[0]
                short_value = row.get('CF_LAST')
                short_name = row.get('CF_NAME', 'N/A')
                short_date = row.get('CF_DATE', 'N/A')
                
                if pd.notna(short_value) and short_value is not None:
                    metal_data['short'] = {
                        'value': float(short_value),
                        'name': short_name,
                        'date': str(short_date),
                        'ric': short_ric
                    }
                    print(f"  ✅ ショート: {short_value:,.2f} ({short_name})")
                else:
                    print(f"  ❌ ショート: データ空")
            else:
                print(f"  ❌ ショート: アクセス失敗 ({short_ric})")
                
            if short_err:
                print(f"    警告: {short_err}")
                
        except Exception as e:
            print(f"  ❌ ショート: エラー - {e}")
        
        time.sleep(0.3)
        
        # ネットポジション計算
        if 'long' in metal_data and 'short' in metal_data:
            long_val = metal_data['long']['value']
            short_val = metal_data['short']['value']
            net_position = long_val - short_val
            
            metal_data['net_position'] = net_position
            metal_data['long_ratio'] = (long_val / (long_val + short_val)) * 100
            metal_data['sentiment'] = _get_sentiment(long_val / short_val if short_val > 0 else float('inf'))
            
            print(f"  📊 ネット: {net_position:,.2f} ({metal_data['sentiment']})")
            
        if metal_data:
            fund_position_data[metal_name.lower()] = metal_data
    
    # 2. 結果サマリー
    print(f"\n\n2. ファンドポジション取得結果サマリー:")
    print("=" * 60)
    
    for metal, data in fund_position_data.items():
        print(f"\n{metal.upper()}:")
        if 'long' in data and 'short' in data:
            print(f"  ロング: {data['long']['value']:,.2f}")
            print(f"  ショート: {data['short']['value']:,.2f}")
            print(f"  ネット: {data['net_position']:,.2f}")
            print(f"  ロング比率: {data['long_ratio']:.1f}%")
            print(f"  センチメント: {data['sentiment']}")
            
            # 市場含意
            net_pos = data['net_position']
            if abs(net_pos) > 10000:
                if net_pos > 0:
                    implication = "大規模ネットロング → 強い上昇圧力"
                else:
                    implication = "大規模ネットショート → 強い下落圧力"
            elif abs(net_pos) > 5000:
                if net_pos > 0:
                    implication = "中規模ネットロング → 上昇傾向"
                else:
                    implication = "中規模ネットショート → 下落傾向"
            else:
                implication = "中立的ポジション → トレンドレス"
            
            print(f"  市場含意: {implication}")
        else:
            available = []
            if 'long' in data:
                available.append("ロング")
            if 'short' in data:
                available.append("ショート")
            print(f"  利用可能: {', '.join(available) if available else 'なし'}")
    
    # 3. Daily Report統合用設定生成
    print(f"\n\n3. Daily Report統合用設定:")
    print("=" * 60)
    
    if fund_position_data:
        # config.jsonに追加する設定を生成
        fund_position_config = {}
        
        for metal, data in fund_position_data.items():
            if 'long' in data and 'short' in data:
                fund_position_config[metal] = {
                    "long_ric": data['long']['ric'],
                    "short_ric": data['short']['ric']
                }
        
        if fund_position_config:
            print("config.jsonに追加する設定:")
            print('"fund_position_rics": {')
            for metal, rics in fund_position_config.items():
                print(f'  "{metal}": {{')
                print(f'    "long_ric": "{rics["long_ric"]}",')
                print(f'    "short_ric": "{rics["short_ric"]}"')
                print(f'  }},')
            print('}')
            
            # Daily Report用サンプル出力
            print(f"\nDaily Report出力サンプル:")
            print("=" * 40)
            print("【投資ファンドポジション（LME）】")
            
            for metal, data in fund_position_data.items():
                if 'long' in data and 'short' in data:
                    print(f"  {metal.capitalize()}:")
                    print(f"    ロング: {data['long']['value']:,.0f} 契約")
                    print(f"    ショート: {data['short']['value']:,.0f} 契約") 
                    print(f"    ネット: {data['net_position']:,.0f} 契約 ({data['sentiment']})")
                    
                    # 前週比較（サンプル）
                    print(f"    更新: {data['long']['date']}")
                    print()
    
    return fund_position_data

def _get_sentiment(long_short_ratio):
    """ロング/ショート比率から市場センチメントを判定"""
    if long_short_ratio > 2.5:
        return "強気バイアス"
    elif long_short_ratio > 1.5:
        return "やや強気"
    elif long_short_ratio > 0.8:
        return "中立"
    elif long_short_ratio > 0.5:
        return "やや弱気"
    else:
        return "弱気バイアス"

if __name__ == "__main__":
    test_all_metals_fund_positions()