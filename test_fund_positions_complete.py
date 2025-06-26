#!/usr/bin/env python3
"""
LME全6金属の投資ファンドポジションRIC調査スクリプト
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

def test_fund_position_rics():
    """全メタルのファンドポジションRICテスト"""
    
    # 設定読み込み
    config = load_config()
    api_key = config.get('eikon_api_key')
    
    if not api_key:
        print("エラー: EIKON APIキーが設定されていません")
        return
    
    # EIKON API初期化
    try:
        ek.set_app_key(api_key)
        print("EIKON API接続成功")
    except Exception as e:
        print(f"EIKON API接続エラー: {e}")
        return
    
    # LME主要6金属のファンドポジション候補RIC
    metals_test_rics = {
        "Copper": {
            "long_ric": "LME-INFUL-CA",
            "short_ric": "LME-INFUS-CA"
        },
        "Aluminium": {
            "long_ric": "LME-INFUL-AL", 
            "short_ric": "LME-INFUS-AL"
        },
        "Zinc": {
            "long_ric": "LME-INFUL-ZN",
            "short_ric": "LME-INFUS-ZN"
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
    
    print("=" * 60)
    print("LME全6金属 投資ファンドポジションRICテスト")
    print("=" * 60)
    
    successful_metals = {}
    failed_metals = {}
    
    for metal_name, rics in metals_test_rics.items():
        print(f"\n【{metal_name}】")
        long_ric = rics["long_ric"]
        short_ric = rics["short_ric"]
        
        metal_success = True
        metal_data = {}
        
        # ロングポジションテスト
        try:
            print(f"  ロングRIC: {long_ric}")
            long_data, long_err = ek.get_data(long_ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
            
            if long_data is not None and not long_data.empty:
                row = long_data.iloc[0]
                long_value = row.get('CF_LAST')
                long_date = row.get('CF_DATE')
                long_name = row.get('CF_NAME')
                
                if pd.notna(long_value) and long_value is not None:
                    print(f"    ✓ ロング: {long_value:,.0f} 契約")
                    print(f"    ✓ 日付: {long_date}")
                    print(f"    ✓ 名称: {long_name}")
                    metal_data['long_value'] = long_value
                    metal_data['long_date'] = str(long_date)
                else:
                    print(f"    ✗ ロングポジション値なし")
                    metal_success = False
            else:
                print(f"    ✗ ロングデータ取得失敗")
                metal_success = False
                
            if long_err:
                print(f"    警告: {long_err}")
                
        except Exception as e:
            print(f"    ✗ ロングRICエラー: {e}")
            metal_success = False
        
        # ショートポジションテスト
        try:
            print(f"  ショートRIC: {short_ric}")
            short_data, short_err = ek.get_data(short_ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
            
            if short_data is not None and not short_data.empty:
                row = short_data.iloc[0]
                short_value = row.get('CF_LAST')
                short_date = row.get('CF_DATE')
                short_name = row.get('CF_NAME')
                
                if pd.notna(short_value) and short_value is not None:
                    print(f"    ✓ ショート: {short_value:,.0f} 契約")
                    print(f"    ✓ 日付: {short_date}")
                    print(f"    ✓ 名称: {short_name}")
                    metal_data['short_value'] = short_value
                    metal_data['short_date'] = str(short_date)
                else:
                    print(f"    ✗ ショートポジション値なし")
                    metal_success = False
            else:
                print(f"    ✗ ショートデータ取得失敗")
                metal_success = False
                
            if short_err:
                print(f"    警告: {short_err}")
                
        except Exception as e:
            print(f"    ✗ ショートRICエラー: {e}")
            metal_success = False
        
        # 結果まとめ
        if metal_success and 'long_value' in metal_data and 'short_value' in metal_data:
            net_position = metal_data['long_value'] - metal_data['short_value']
            total_position = metal_data['long_value'] + metal_data['short_value']
            long_ratio = (metal_data['long_value'] / total_position) * 100 if total_position > 0 else 0
            
            print(f"    ネットポジション: {net_position:+,.0f} 契約")
            print(f"    ロング比率: {long_ratio:.1f}%")
            
            successful_metals[metal_name] = {
                "long_ric": long_ric,
                "short_ric": short_ric,
                "test_data": metal_data
            }
            print(f"    → {metal_name} ファンドポジションRIC: 有効")
            
        else:
            failed_metals[metal_name] = {
                "long_ric": long_ric,
                "short_ric": short_ric,
                "error": "データ取得失敗"
            }
            print(f"    → {metal_name} ファンドポジションRIC: 無効")
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    print(f"\n✓ 成功したメタル ({len(successful_metals)}/6):")
    for metal in successful_metals.keys():
        print(f"  - {metal}")
    
    if failed_metals:
        print(f"\n✗ 失敗したメタル ({len(failed_metals)}/6):")
        for metal, info in failed_metals.items():
            print(f"  - {metal}: {info['error']}")
    
    # config.json用の設定生成
    if successful_metals:
        print(f"\n📋 config.json用設定:")
        config_section = {}
        for metal, info in successful_metals.items():
            config_section[metal] = {
                "long_ric": info["long_ric"],
                "short_ric": info["short_ric"]
            }
        
        print(json.dumps(config_section, indent=2, ensure_ascii=False))
    
    return successful_metals, failed_metals

if __name__ == "__main__":
    try:
        successful, failed = test_fund_position_rics()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)