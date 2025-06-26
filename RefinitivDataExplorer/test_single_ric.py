#!/usr/bin/env python3
"""
Single RIC Test for Warrant Data
ユーザー発見のRIC /MCUSTX-TOTAL:GEN_VAL3 の詳細テスト

Author: Claude Code  
Created: 2025-06-26
"""

import eikon as ek
import pandas as pd
import json

def test_single_ric():
    """単一RICの詳細テスト"""
    
    # 設定読み込み
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # EIKON API初期化
    ek.set_app_key(config["eikon_api_key"])
    
    print("🔍 ユーザー発見RICの詳細テスト")
    print("=" * 50)
    
    # ユーザーが発見したRIC
    test_ric = "/MCUSTX-TOTAL:GEN_VAL3"
    print(f"テストRIC: {test_ric}")
    print(f"期待値: 56250 (OnWarrant)")
    print("=" * 50)
    
    # 1. 基本的なフィールドテスト
    print("\n1. 基本フィールドテスト:")
    try:
        basic_fields = ['CF_LAST', 'CF_CLOSE', 'CF_NAME', 'CF_DATE', 'CF_TIME']
        data, err = ek.get_data(test_ric, basic_fields)
        print(f"基本データ:\n{data}")
        if err:
            print(f"エラー: {err}")
    except Exception as e:
        print(f"基本フィールドエラー: {e}")
    
    # 2. GEN_VALフィールド個別テスト
    print("\n2. GEN_VALフィールド個別テスト:")
    for i in range(1, 6):
        try:
            field = f'GEN_VAL{i}'
            data, err = ek.get_data(test_ric, [field])
            print(f"{field}: {data.iloc[0][field] if not data.empty else 'Empty'}")
        except Exception as e:
            print(f"{field} エラー: {e}")
    
    # 3. 全フィールド一括テスト
    print("\n3. 全フィールド一括取得:")
    try:
        all_fields = ['CF_LAST', 'CF_CLOSE', 'CF_NAME', 'CF_DATE', 'CF_TIME', 
                     'GEN_VAL1', 'GEN_VAL2', 'GEN_VAL3', 'GEN_VAL4', 'GEN_VAL5',
                     'GEN_TEXT1', 'GEN_TEXT2', 'GEN_TEXT3']
        data, err = ek.get_data(test_ric, all_fields)
        print("全フィールドデータ:")
        if not data.empty:
            for col in data.columns:
                value = data.iloc[0][col]
                if pd.notna(value) and value is not None:
                    print(f"  {col}: {value}")
        if err:
            print(f"エラー: {err}")
    except Exception as e:
        print(f"全フィールドエラー: {e}")
    
    # 4. 代替RICテスト
    print("\n4. 代替RICパターンテスト:")
    alt_rics = [
        "MCUSTX-TOTAL:GEN_VAL3",  # スラッシュなし
        "MCUSTX-TOTAL.GEN_VAL3",  # ドット記法
        "/MCUSTX:GEN_VAL3",       # 短縮形
        "CMCU-STX:GEN_VAL3"       # 別パターン
    ]
    
    for alt_ric in alt_rics:
        try:
            data, err = ek.get_data(alt_ric, ['CF_LAST', 'GEN_VAL3'])
            cf_last = data.iloc[0]['CF_LAST'] if not data.empty and 'CF_LAST' in data.columns else None
            gen_val3 = data.iloc[0]['GEN_VAL3'] if not data.empty and 'GEN_VAL3' in data.columns else None
            print(f"{alt_ric}: CF_LAST={cf_last}, GEN_VAL3={gen_val3}")
        except Exception as e:
            print(f"{alt_ric}: エラー - {e}")
    
    # 5. 関連する在庫RICテスト
    print("\n5. 関連在庫RICテスト:")
    stock_rics = [
        "MCUSTX-TOTAL",      # 基本形
        "/MCUSTX-TOTAL",     # スラッシュ付き
        "CMCU-STX-LME",      # LME在庫
        "LMCUSTX",           # LME銅在庫
    ]
    
    for stock_ric in stock_rics:
        try:
            data, err = ek.get_data(stock_ric, ['CF_LAST', 'CF_NAME'])
            value = data.iloc[0]['CF_LAST'] if not data.empty else None
            name = data.iloc[0]['CF_NAME'] if not data.empty else None
            print(f"{stock_ric}: {value} ({name})")
        except Exception as e:
            print(f"{stock_ric}: エラー - {e}")

if __name__ == "__main__":
    test_single_ric()