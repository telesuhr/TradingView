#!/usr/bin/env python3
"""
All Warrant Pattern Test
全金属のワラントパターンテスト

Author: Claude Code  
Created: 2025-06-26
"""

import eikon as ek
import pandas as pd
import json

def test_all_warrant_patterns():
    """全金属のワラントパターンテスト"""
    
    # 設定読み込み
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # EIKON API初期化
    ek.set_app_key(config["eikon_api_key"])
    
    print("🎯 全金属ワラントパターン完全テスト")
    print("=" * 60)
    print("発見パターン: [BASE_RIC]:[GEN_VAL_FIELD] → ek.get_data(BASE_RIC, [GEN_VAL_FIELD])")
    print("=" * 60)
    
    # 金属別のベースRICパターン
    metals_base_rics = {
        "copper": [
            "MCUSTX-TOTAL",
            "/MCUSTX-TOTAL",
            "MCUSTX",
            "/MCUSTX"
        ],
        "aluminum": [
            "MALSTX-TOTAL", 
            "/MALSTX-TOTAL",
            "MALSTX",
            "/MALSTX"
        ],
        "zinc": [
            "MZNSTX-TOTAL",
            "/MZNSTX-TOTAL", 
            "MZNSTX",
            "/MZNSTX"
        ],
        "lead": [
            "MPBSTX-TOTAL",
            "/MPBSTX-TOTAL",
            "MPBSTX", 
            "/MPBSTX"
        ],
        "nickel": [
            "MNISTX-TOTAL",
            "/MNISTX-TOTAL",
            "MNISTX",
            "/MNISTX"
        ],
        "tin": [
            "MSNSTX-TOTAL",
            "/MSNSTX-TOTAL",
            "MSNSTX",
            "/MSNSTX"
        ]
    }
    
    # GEN_VALフィールドの意味推定
    gen_val_meanings = {
        "GEN_VAL1": "cancelled_warrants",   # キャンセルワラント
        "GEN_VAL2": "on_warrant",           # オンワラント  
        "GEN_VAL3": "total_stock",          # 総在庫（ユーザー発見）
        "GEN_VAL4": "live_warrants",        # ライブワラント
        "GEN_VAL5": "other_field"           # その他
    }
    
    results = {}
    
    for metal, base_rics in metals_base_rics.items():
        print(f"\n🔍 {metal.upper()}ワラントデータテスト:")
        results[metal] = {}
        
        # 各ベースRICをテスト
        working_ric = None
        for base_ric in base_rics:
            try:
                # GEN_VAL1-5をまとめてテスト
                test_data, err = ek.get_data(base_ric, ['GEN_VAL1', 'GEN_VAL2', 'GEN_VAL3', 'GEN_VAL4', 'GEN_VAL5', 'CF_NAME'])
                
                if not test_data.empty:
                    row = test_data.iloc[0]
                    name = row.get('CF_NAME', 'N/A')
                    
                    # 有効な値があるか確認
                    valid_values = {}
                    for i in range(1, 6):
                        field = f'GEN_VAL{i}'
                        value = row.get(field)
                        if pd.notna(value) and value is not None and value != 0:
                            valid_values[field] = value
                    
                    if valid_values:
                        working_ric = base_ric
                        results[metal]['base_ric'] = base_ric
                        results[metal]['name'] = name
                        results[metal]['values'] = valid_values
                        
                        print(f"  ✅ 成功RIC: {base_ric} ({name})")
                        
                        # 各値の詳細表示
                        for field, value in valid_values.items():
                            meaning = gen_val_meanings.get(field, "unknown")
                            print(f"    {field} ({meaning}): {value:,}")
                            
                            # 特に大きな値（在庫らしい値）をハイライト
                            if isinstance(value, (int, float)) and value > 10000:
                                print(f"      *** 在庫候補: {value:,} トン ***")
                        
                        break  # 成功したRICが見つかったらループを抜ける
                        
            except Exception as e:
                print(f"  ❌ {base_ric}: エラー - {e}")
        
        if not working_ric:
            print(f"  ⚠️  {metal}: 有効なRICが見つかりませんでした")
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 ワラントデータ取得結果サマリー")
    print("=" * 60)
    
    for metal, data in results.items():
        if data:
            print(f"\n{metal.upper()}:")
            print(f"  有効RIC: {data['base_ric']}")
            print(f"  名称: {data['name']}")
            
            values = data['values']
            
            # ワラント構造分析
            total_stock = values.get('GEN_VAL3')  # ユーザー発見の総在庫
            on_warrant = values.get('GEN_VAL2')   # オンワラント推定
            cancelled = values.get('GEN_VAL1')   # キャンセル推定
            
            if total_stock:
                print(f"  総在庫 (GEN_VAL3): {total_stock:,} トン")
            if on_warrant:
                print(f"  オンワラント (GEN_VAL2): {on_warrant:,} トン")
            if cancelled:
                print(f"  キャンセル (GEN_VAL1): {cancelled:,} トン")
            
            # キャンセル率計算
            if total_stock and cancelled and isinstance(total_stock, (int, float)) and isinstance(cancelled, (int, float)):
                cancel_rate = (cancelled / total_stock) * 100
                print(f"  キャンセル率: {cancel_rate:.1f}%")
                
                if cancel_rate > 15:
                    print(f"    → 高キャンセル率: バックワーデーション圧力")
                elif cancel_rate > 5:
                    print(f"    → 中程度キャンセル率: 現物需要あり")
                else:
                    print(f"    → 低キャンセル率: 需給緩和")
    
    # Daily Reportへの統合提案
    print("\n" + "=" * 60)
    print("🔧 Daily Report統合用RICコード")
    print("=" * 60)
    
    print("# 発見されたワラント詳細RICパターン")
    for metal, data in results.items():
        if data:
            base_ric = data['base_ric']
            print(f"\"{metal}_warrant_detail\": {{")
            print(f"    \"base_ric\": \"{base_ric}\",")
            print(f"    \"total_stock\": \"{base_ric}:GEN_VAL3\",")
            print(f"    \"on_warrant\": \"{base_ric}:GEN_VAL2\",") 
            print(f"    \"cancelled_warrants\": \"{base_ric}:GEN_VAL1\",")
            print(f"    \"live_warrants\": \"{base_ric}:GEN_VAL4\"")
            print(f"}},")

if __name__ == "__main__":
    test_all_warrant_patterns()