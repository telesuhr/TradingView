#!/usr/bin/env python3
"""
LME全6金属の完全なファンドポジションデータ取得テスト
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

def test_complete_fund_positions():
    """全6金属の完全なファンドポジションテスト"""
    
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
    
    # 全6金属の確認済み有効RIC
    complete_fund_rics = {
        "Copper": {
            "long_ric": "LME-INFUL-CA",
            "short_ric": "LME-INFUS-CA"
        },
        "Aluminium": {
            "long_ric": "LME-INFUL-AH",
            "short_ric": "LME-INFUS-AH"
        },
        "Zinc": {
            "long_ric": "LME-INFUL-ZS",
            "short_ric": "LME-INFUS-ZS"
        },
        "Lead": {
            "long_ric": "LME-INFUL-PB",
            "short_ric": "LME-INFUS-PB"
        },
        "Nickel": {
            "long_ric": "LME-INFUL-NI",
            "short_ric": "LME-INFUS-NI"
        },
        "Tin": {
            "long_ric": "LME-INFUL-SN",
            "short_ric": "LME-INFUS-SN"
        }
    }
    
    print("=" * 70)
    print("LME全6金属 完全ファンドポジションデータ取得テスト")
    print("=" * 70)
    
    fund_position_data = {}
    
    for metal_name, rics in complete_fund_rics.items():
        print(f"\n【{metal_name}】")
        
        try:
            long_ric = rics.get("long_ric")
            short_ric = rics.get("short_ric")
            
            # ロングポジション取得
            long_value = None
            long_date = None
            try:
                long_data, long_err = ek.get_data(long_ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                if long_data is not None and not long_data.empty:
                    row = long_data.iloc[0]
                    long_value = row.get('CF_LAST')
                    long_date = row.get('CF_DATE')
                    long_name = row.get('CF_NAME')
                    if pd.notna(long_value) and long_value is not None:
                        print(f"  ロングポジション: {long_value:,.0f} 契約")
                        print(f"  ロング名称: {long_name}")
                    else:
                        long_value = None
                if long_err:
                    print(f"  ロング警告: {long_err}")
            except Exception as long_error:
                print(f"  ロングポジション取得エラー: {long_error}")
            
            # ショートポジション取得
            short_value = None
            short_date = None
            try:
                short_data, short_err = ek.get_data(short_ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                if short_data is not None and not short_data.empty:
                    row = short_data.iloc[0]
                    short_value = row.get('CF_LAST')
                    short_date = row.get('CF_DATE')
                    short_name = row.get('CF_NAME')
                    if pd.notna(short_value) and short_value is not None:
                        print(f"  ショートポジション: {short_value:,.0f} 契約")
                        print(f"  ショート名称: {short_name}")
                    else:
                        short_value = None
                if short_err:
                    print(f"  ショート警告: {short_err}")
            except Exception as short_error:
                print(f"  ショートポジション取得エラー: {short_error}")
            
            # データが両方取得できた場合の分析
            if long_value is not None and short_value is not None:
                net_position = long_value - short_value
                total_position = long_value + short_value
                long_ratio = (long_value / total_position) * 100 if total_position > 0 else 0
                
                # センチメント判定
                if total_position > 0:
                    ls_ratio = long_value / short_value
                    if ls_ratio > 2.5:
                        sentiment = "強気バイアス"
                    elif ls_ratio > 1.5:
                        sentiment = "やや強気"
                    elif ls_ratio > 0.8:
                        sentiment = "中立"
                    elif ls_ratio > 0.5:
                        sentiment = "やや弱気"
                    else:
                        sentiment = "弱気バイアス"
                else:
                    sentiment = "データ不足"
                
                print(f"  ネットポジション: {net_position:+,.0f} 契約")
                print(f"  ロング比率: {long_ratio:.1f}%")
                print(f"  センチメント: {sentiment}")
                print(f"  最終更新: {long_date}")
                
                # 市場含意分析
                if abs(net_position) > 20000:
                    if net_position > 0:
                        implication = "大規模ネットロング → 強い上昇圧力"
                    else:
                        implication = "大規模ネットショート → 強い下落圧力"
                elif abs(net_position) > 10000:
                    if net_position > 0:
                        implication = "中規模ネットロング → 上昇傾向"
                    else:
                        implication = "中規模ネットショート → 下落傾向"
                else:
                    implication = "中立的ポジション → トレンドレス"
                
                print(f"  市場含意: {implication}")
                
                fund_position_data[metal_name] = {
                    'long_position': long_value,
                    'short_position': short_value,
                    'net_position': net_position,
                    'long_ratio': long_ratio,
                    'sentiment': sentiment,
                    'market_implication': implication,
                    'last_updated': str(long_date) if long_date else str(short_date)
                }
                
                print(f"  → {metal_name}: データ取得成功")
            else:
                print(f"  → {metal_name}: データ取得失敗")
                
        except Exception as e:
            print(f"  {metal_name}エラー: {e}")
    
    # 全体サマリー
    print("\n" + "=" * 70)
    print("ファンドポジション分析サマリー")
    print("=" * 70)
    
    if fund_position_data:
        print(f"\n成功取得: {len(fund_position_data)}/6 金属")
        
        # センチメント別分類
        sentiment_groups = {}
        for metal, data in fund_position_data.items():
            sentiment = data['sentiment']
            if sentiment not in sentiment_groups:
                sentiment_groups[sentiment] = []
            sentiment_groups[sentiment].append(metal)
        
        print("\nセンチメント別分類:")
        for sentiment, metals in sentiment_groups.items():
            print(f"  {sentiment}: {', '.join(metals)}")
        
        # ネットポジション上位3位
        net_positions = [(metal, data['net_position']) for metal, data in fund_position_data.items()]
        net_positions.sort(key=lambda x: x[1], reverse=True)
        
        print("\nネットポジション順位:")
        for i, (metal, net_pos) in enumerate(net_positions, 1):
            print(f"  {i}. {metal}: {net_pos:+,.0f} 契約")
        
        print(f"\n📋 config.json完全版:")
        print(json.dumps(complete_fund_rics, indent=2, ensure_ascii=False))
        
    else:
        print("全金属でデータ取得に失敗しました")
    
    return fund_position_data

if __name__ == "__main__":
    try:
        result = test_complete_fund_positions()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)