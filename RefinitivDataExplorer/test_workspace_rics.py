#!/usr/bin/env python3
"""
Workspace-style RIC Access Test
Workspaceで表示される形式でのRICアクセステスト

Author: Claude Code  
Created: 2025-06-26
"""

import eikon as ek
import pandas as pd
import json

def test_workspace_access():
    """Workspaceスタイルでのアクセステスト"""
    
    # 設定読み込み
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # EIKON API初期化
    ek.set_app_key(config["eikon_api_key"])
    
    print("🏢 Workspaceスタイル RICアクセステスト")
    print("=" * 60)
    print("発見情報: /MCUSTX-TOTAL:GEN_VAL3, GEN VAL3, 998")
    print("期待値: 56250")
    print("=" * 60)
    
    # 1. 基本RICのテスト
    print("\n1. 基本RIC単体テスト:")
    base_rics = [
        "MCUSTX-TOTAL",
        "/MCUSTX-TOTAL", 
        "MCUSTX/TOTAL",
        "MCU.STX.TOTAL"
    ]
    
    for ric in base_rics:
        try:
            # 複数のフィールドパターンを試行
            fields_to_try = [
                ['GEN_VAL3'],
                ['CF_LAST'],
                ['CLOSE'],
                ['VALUE'],
                ['GEN_VAL1', 'GEN_VAL2', 'GEN_VAL3', 'GEN_VAL4', 'GEN_VAL5'],
                ['CF_LAST', 'CF_CLOSE', 'CF_NAME']
            ]
            
            print(f"\n  RIC: {ric}")
            for fields in fields_to_try:
                try:
                    data, err = ek.get_data(ric, fields)
                    if not data.empty:
                        for col in data.columns:
                            if col != 'Instrument':
                                value = data.iloc[0][col]
                                if pd.notna(value) and value is not None:
                                    print(f"    {col}: {value}")
                                    if isinstance(value, (int, float)) and 50000 <= value <= 60000:
                                        print(f"    *** 期待値に近い! {value} ***")
                    break  # 成功したらループを抜ける
                except:
                    continue
        except Exception as e:
            print(f"  {ric}: 全体エラー - {e}")
    
    # 2. 直接値アクセステスト
    print("\n2. 直接値アクセステスト:")
    direct_patterns = [
        "/MCUSTX-TOTAL:GEN_VAL3",
        "MCUSTX-TOTAL:GEN_VAL3", 
        "/MCUSTX.TOTAL:GEN_VAL3",
        "MCUSTX.TOTAL:GEN_VAL3"
    ]
    
    for pattern in direct_patterns:
        try:
            # get_dataの代わりにget_timeseriesを試行
            print(f"\n  パターン: {pattern}")
            
            # 方法1: get_data
            try:
                data, err = ek.get_data(pattern, ['CF_LAST', 'VALUE', 'CLOSE'])
                if not data.empty:
                    print(f"    get_data成功: {data.to_dict('records')[0]}")
            except Exception as e1:
                print(f"    get_data失敗: {e1}")
            
            # 方法2: 単一値取得として試行
            try:
                # RICを楽器として扱い、値フィールドとして取得
                import time
                time.sleep(0.2)
                data2, err2 = ek.get_data(pattern.split(':')[0], [pattern.split(':')[1] if ':' in pattern else 'CF_LAST'])
                if not data2.empty:
                    print(f"    分割アクセス成功: {data2.to_dict('records')[0]}")
            except Exception as e2:
                print(f"    分割アクセス失敗: {e2}")
                
        except Exception as e:
            print(f"    {pattern}: エラー - {e}")
    
    # 3. チェーンベースでの検索
    print("\n3. チェーンベースでの在庫検索:")
    chain_rics = [
        "0#LME-CU-STK",     # LME銅在庫チェーン
        "0#LME-STOCKS",     # LME全在庫チェーン
        "0#MCUSTX",         # 銅在庫関連チェーン
        "0#LME-CU"          # LME銅関連チェーン
    ]
    
    for chain in chain_rics:
        try:
            print(f"\n  チェーン: {chain}")
            data, err = ek.get_data(chain, ['CF_LAST', 'CF_NAME', 'GEN_VAL3'])
            if not data.empty:
                print(f"    件数: {len(data)}")
                for _, row in data.iterrows():
                    name = row.get('CF_NAME', 'N/A')
                    value = row.get('CF_LAST', 'N/A')
                    gen_val3 = row.get('GEN_VAL3', 'N/A')
                    
                    # 56250に近い値を探す
                    if isinstance(value, (int, float)) and 50000 <= value <= 60000:
                        print(f"    *** 候補発見: {name} = {value} (GEN_VAL3: {gen_val3}) ***")
                    elif pd.notna(value) and value != 'N/A':
                        print(f"    {name}: {value} (GEN_VAL3: {gen_val3})")
            else:
                print(f"    データなし (エラー: {err})")
        except Exception as e:
            print(f"    {chain}: エラー - {e}")
    
    # 4. LME在庫の詳細検索
    print("\n4. LME在庫詳細検索:")
    lme_patterns = [
        "LME-CU-TOT",       # LME銅総在庫
        "LME-CU-ON",        # LME銅オンワラント
        "LME-CU-CAN",       # LME銅キャンセル
        "LME-CU-LIVE",      # LME銅ライブ
        "LMCUSTX",          # LME銅在庫
        "LMCSTX",           # LME銅在庫（短縮）
        "CU-STK-LME"        # 銅在庫LME
    ]
    
    for pattern in lme_patterns:
        try:
            data, err = ek.get_data(pattern, ['CF_LAST', 'CF_NAME', 'VALUE', 'CLOSE'])
            if not data.empty:
                row = data.iloc[0]
                name = row.get('CF_NAME', 'N/A')
                values = {col: row.get(col, 'N/A') for col in ['CF_LAST', 'VALUE', 'CLOSE'] if pd.notna(row.get(col))}
                
                print(f"  {pattern}: {name}")
                for field, value in values.items():
                    if isinstance(value, (int, float)) and 50000 <= value <= 60000:
                        print(f"    *** {field}: {value} (期待値に近い!) ***")
                    elif pd.notna(value) and value != 'N/A':
                        print(f"    {field}: {value}")
            else:
                print(f"  {pattern}: データなし")
        except Exception as e:
            print(f"  {pattern}: エラー - {e}")

if __name__ == "__main__":
    test_workspace_access()