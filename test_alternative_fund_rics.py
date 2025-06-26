#!/usr/bin/env python3
"""
アルミニウムと亜鉛の代替ファンドポジションRIC探索
"""

import sys
import json
import eikon as ek
import pandas as pd

def load_config():
    """設定ファイル読み込み"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

def test_alternative_rics():
    """アルミニウムと亜鉛の代替RICテスト"""
    
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
    
    # 代替RICパターン候補
    alternative_patterns = {
        "Aluminium": [
            {"long_ric": "LME-INFUL-AH", "short_ric": "LME-INFUS-AH"},  # AH = Aluminium High Grade
            {"long_ric": "LME-INFUL-AA", "short_ric": "LME-INFUS-AA"},  # AA = Aluminium Alloy
            {"long_ric": "LMAHD-INFUL", "short_ric": "LMAHD-INFUS"},    # LME Aluminium High Grade
        ],
        "Zinc": [
            {"long_ric": "LME-INFUL-ZS", "short_ric": "LME-INFUS-ZS"},  # ZS = Zinc Special
            {"long_ric": "LME-INFUL-ZI", "short_ric": "LME-INFUS-ZI"},  # ZI = Zinc Integer
            {"long_ric": "LMZSD-INFUL", "short_ric": "LMZSD-INFUS"},    # LME Zinc Special
        ]
    }
    
    print("=" * 60)
    print("アルミニウム・亜鉛代替ファンドポジションRIC探索")
    print("=" * 60)
    
    successful_alternatives = {}
    
    for metal_name, patterns in alternative_patterns.items():
        print(f"\n【{metal_name}】")
        
        for i, pattern in enumerate(patterns, 1):
            print(f"\n  パターン{i}: {pattern['long_ric']} / {pattern['short_ric']}")
            
            try:
                # ロングポジションテスト
                long_data, long_err = ek.get_data(pattern['long_ric'], ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                long_success = False
                
                if long_data is not None and not long_data.empty:
                    row = long_data.iloc[0]
                    long_value = row.get('CF_LAST')
                    if pd.notna(long_value) and long_value is not None:
                        print(f"    ✓ ロング: {long_value:,.0f} 契約")
                        long_success = True
                    else:
                        print(f"    ✗ ロング値なし")
                else:
                    print(f"    ✗ ロングデータなし")
                
                if long_err:
                    print(f"    ロング警告: {long_err}")
                
                # ショートポジションテスト
                short_data, short_err = ek.get_data(pattern['short_ric'], ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                short_success = False
                
                if short_data is not None and not short_data.empty:
                    row = short_data.iloc[0]
                    short_value = row.get('CF_LAST')
                    if pd.notna(short_value) and short_value is not None:
                        print(f"    ✓ ショート: {short_value:,.0f} 契約")
                        short_success = True
                    else:
                        print(f"    ✗ ショート値なし")
                else:
                    print(f"    ✗ ショートデータなし")
                
                if short_err:
                    print(f"    ショート警告: {short_err}")
                
                if long_success and short_success:
                    print(f"    → パターン{i}: 成功!")
                    successful_alternatives[metal_name] = pattern
                    break
                else:
                    print(f"    → パターン{i}: 失敗")
                    
            except Exception as e:
                print(f"    → パターン{i}: エラー - {e}")
        
        if metal_name not in successful_alternatives:
            print(f"  → {metal_name}: 全パターン失敗")
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("代替RIC探索結果")
    print("=" * 60)
    
    if successful_alternatives:
        print("\n✓ 見つかった代替RIC:")
        for metal, rics in successful_alternatives.items():
            print(f"  {metal}: {rics['long_ric']} / {rics['short_ric']}")
    else:
        print("\n✗ 有効な代替RICが見つかりませんでした")
    
    return successful_alternatives

if __name__ == "__main__":
    try:
        result = test_alternative_rics()
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)