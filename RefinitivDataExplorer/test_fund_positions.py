#!/usr/bin/env python3
"""
Test Fund Position Data
ファンドポジションデータテスト

Author: Claude Code  
Created: 2025-06-26
"""

import eikon as ek
import pandas as pd
import json
import time

def test_fund_positions():
    """ファンドポジションデータテスト"""
    
    # 設定読み込み
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # EIKON API初期化
    ek.set_app_key(config["eikon_api_key"])
    
    print("📊 LMEファンドポジションデータテスト")
    print("=" * 60)
    print("発見RIC:")
    print("- InFnd Short TOT: LME-INFUS-CA (29948.27)")
    print("- InFnd Long TOT: LME-INFUL-CA (62742.55)")
    print("=" * 60)
    
    # 発見されたファンドポジションRIC
    fund_position_rics = {
        "investment_fund_short_total": "LME-INFUS-CA",
        "investment_fund_long_total": "LME-INFUL-CA"
    }
    
    # 1. 基本的なデータ取得テスト
    print("\n1. 基本データ取得テスト:")
    print("-" * 40)
    
    fund_data = {}
    
    for position_type, ric in fund_position_rics.items():
        print(f"\n{position_type} ({ric}):")
        try:
            # 基本フィールドでテスト
            basic_fields = ['CF_LAST', 'CF_CLOSE', 'CF_NAME', 'CF_DATE', 'CF_TIME']
            data, err = ek.get_data(ric, basic_fields)
            
            if data is not None and not data.empty:
                row = data.iloc[0]
                
                name = row.get('CF_NAME', 'N/A')
                value = row.get('CF_LAST')
                date = row.get('CF_DATE', 'N/A')
                
                print(f"  名称: {name}")
                print(f"  値: {value}")
                print(f"  日付: {date}")
                
                if pd.notna(value) and value is not None:
                    fund_data[position_type] = {
                        'value': float(value),
                        'name': name,
                        'date': str(date),
                        'ric': ric
                    }
                    
                    # 期待値との比較
                    if position_type == "investment_fund_short_total" and abs(float(value) - 29948.27) < 1000:
                        print(f"  ✅ 期待値(29948.27)に近い！差異: {abs(float(value) - 29948.27):.2f}")
                    elif position_type == "investment_fund_long_total" and abs(float(value) - 62742.55) < 1000:
                        print(f"  ✅ 期待値(62742.55)に近い！差異: {abs(float(value) - 62742.55):.2f}")
                
            else:
                print(f"  ❌ データなし")
                
            if err:
                print(f"  警告: {err}")
                
        except Exception as e:
            print(f"  ❌ エラー: {e}")
        
        time.sleep(0.3)
    
    # 2. 詳細フィールドテスト
    print("\n\n2. 詳細フィールドテスト:")
    print("-" * 40)
    
    for position_type, ric in fund_position_rics.items():
        print(f"\n{position_type} ({ric}):")
        try:
            # より多くのフィールドを試行
            extended_fields = [
                'CF_LAST', 'CF_CLOSE', 'CF_NAME', 'CF_DATE', 'CF_TIME',
                'VALUE', 'CLOSE', 'HIGH', 'LOW', 'OPEN',
                'GEN_VAL1', 'GEN_VAL2', 'GEN_VAL3', 'GEN_VAL4', 'GEN_VAL5'
            ]
            
            data, err = ek.get_data(ric, extended_fields)
            
            if data is not None and not data.empty:
                row = data.iloc[0]
                
                print(f"  利用可能フィールド:")
                for field in extended_fields:
                    if field in row:
                        value = row.get(field)
                        if pd.notna(value) and value is not None and str(value) != '<NA>':
                            print(f"    {field}: {value}")
            
        except Exception as e:
            print(f"  詳細フィールドエラー: {e}")
        
        time.sleep(0.3)
    
    # 3. 関連RICパターン探索
    print("\n\n3. 関連RICパターン探索:")
    print("-" * 40)
    
    # 類似パターンを試行
    related_patterns = [
        "LME-INFUS",      # 短縮形
        "LME-INFUL",      # 短縮形
        "LME-INFUS-CU",   # 銅特化
        "LME-INFUL-CU",   # 銅特化
        "LME-INFUS-AL",   # アルミ特化
        "LME-INFUL-AL",   # アルミ特化
        "LME-INF-NET",    # ネットポジション
        "LME-INF-TOT",    # 総ポジション
    ]
    
    for pattern in related_patterns:
        try:
            data, err = ek.get_data(pattern, ['CF_LAST', 'CF_NAME'])
            if data is not None and not data.empty:
                row = data.iloc[0]
                name = row.get('CF_NAME', 'N/A')
                value = row.get('CF_LAST')
                if pd.notna(value):
                    print(f"  ✅ {pattern}: {value} ({name})")
            else:
                print(f"  ❌ {pattern}: データなし")
        except Exception as e:
            print(f"  ❌ {pattern}: エラー - {e}")
        
        time.sleep(0.2)
    
    # 4. ネットポジション計算
    print("\n\n4. ファンドポジション分析:")
    print("-" * 40)
    
    if len(fund_data) >= 2:
        short_data = fund_data.get("investment_fund_short_total")
        long_data = fund_data.get("investment_fund_long_total")
        
        if short_data and long_data:
            short_value = short_data['value']
            long_value = long_data['value']
            net_position = long_value - short_value
            
            print(f"📊 ファンドポジション分析:")
            print(f"  ロングポジション: {long_value:,.2f}")
            print(f"  ショートポジション: {short_value:,.2f}")
            print(f"  ネットポジション: {net_position:,.2f}")
            print(f"  ロング比率: {(long_value / (long_value + short_value)) * 100:.1f}%")
            print(f"  ショート比率: {(short_value / (long_value + short_value)) * 100:.1f}%")
            
            # 市場含意
            long_short_ratio = long_value / short_value if short_value > 0 else float('inf')
            print(f"  ロング/ショート比率: {long_short_ratio:.2f}")
            
            if long_short_ratio > 2.5:
                sentiment = "強気バイアス（ロング優勢）"
            elif long_short_ratio > 1.5:
                sentiment = "やや強気バイアス"
            elif long_short_ratio > 0.8:
                sentiment = "中立的ポジション"
            elif long_short_ratio > 0.5:
                sentiment = "やや弱気バイアス"
            else:
                sentiment = "弱気バイアス（ショート優勢）"
            
            print(f"  市場センチメント: {sentiment}")
            
            # 金額ベース分析（仮にコントラクト単位と仮定）
            if net_position > 10000:
                implication = "大規模ネットロング → 上昇圧力"
            elif net_position > 5000:
                implication = "中程度ネットロング → 上昇傾向"
            elif net_position > -5000:
                implication = "中立的ポジション → トレンドレス"
            elif net_position > -10000:
                implication = "中程度ネットショート → 下落傾向"
            else:
                implication = "大規模ネットショート → 下落圧力"
            
            print(f"  市場含意: {implication}")
    
    # 5. Daily Report統合用データ構造
    print("\n\n5. Daily Report統合用データ構造:")
    print("-" * 40)
    
    if fund_data:
        print("Daily Report統合用JSON:")
        integration_data = {
            "fund_positions": {
                "copper_investment_funds": {
                    "long_position": fund_data.get("investment_fund_long_total", {}).get('value'),
                    "short_position": fund_data.get("investment_fund_short_total", {}).get('value'),
                    "net_position": (fund_data.get("investment_fund_long_total", {}).get('value', 0) - 
                                   fund_data.get("investment_fund_short_total", {}).get('value', 0)),
                    "long_ric": "LME-INFUL-CA",
                    "short_ric": "LME-INFUS-CA",
                    "last_updated": fund_data.get("investment_fund_long_total", {}).get('date')
                }
            }
        }
        
        print(json.dumps(integration_data, indent=2, ensure_ascii=False))
    
    print("\n✅ ファンドポジションテスト完了")
    print("🎯 Daily Reportへの統合準備完了")

if __name__ == "__main__":
    test_fund_positions()