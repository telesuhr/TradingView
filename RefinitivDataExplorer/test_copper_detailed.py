#!/usr/bin/env python3
"""
Copper Detailed Warrant Analysis
銅ワラントの詳細分析 - ユーザー発見の追加フィールド検証

Author: Claude Code  
Created: 2025-06-26
"""

import eikon as ek
import pandas as pd
import json

def test_copper_detailed_warrants():
    """銅ワラントの詳細分析"""
    
    # 設定読み込み
    with open("config.json", 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # EIKON API初期化
    ek.set_app_key(config["eikon_api_key"])
    
    print("🔍 銅ワラント詳細分析 - ユーザー発見フィールド検証")
    print("=" * 60)
    print("新発見情報:")
    print("- キャンセルワラント: GEN_VAL4")
    print("- キャンセルワラント比率: GEN_VAL7")
    print("=" * 60)
    
    # 銅の基本RIC
    copper_ric = "MCUSTX-TOTAL"
    
    # 1. 全GEN_VALフィールドを取得 (1-10まで)
    print(f"\n1. 全GEN_VALフィールド取得: {copper_ric}")
    print("-" * 40)
    
    try:
        # GEN_VAL1からGEN_VAL10まで取得
        gen_val_fields = [f'GEN_VAL{i}' for i in range(1, 11)]
        data, err = ek.get_data(copper_ric, gen_val_fields + ['CF_NAME', 'CF_DATE'])
        
        if not data.empty:
            row = data.iloc[0]
            name = row.get('CF_NAME', 'N/A')
            date = row.get('CF_DATE', 'N/A')
            
            print(f"RIC名称: {name}")
            print(f"更新日: {date}")
            print()
            
            # 各GEN_VALフィールドの値を表示
            copper_values = {}
            for i in range(1, 11):
                field = f'GEN_VAL{i}'
                value = row.get(field)
                if pd.notna(value) and value is not None:
                    copper_values[field] = value
                    print(f"{field}: {value:,}")
                else:
                    print(f"{field}: N/A")
            
            print()
            
        if err:
            print(f"エラー: {err}")
            
    except Exception as e:
        print(f"取得エラー: {e}")
    
    # 2. ユーザー発見の構造検証
    print("2. ワラント構造分析:")
    print("-" * 40)
    
    if 'copper_values' in locals():
        # 既知の値
        gen_val1 = copper_values.get('GEN_VAL1')  # 前回: 1,725
        gen_val2 = copper_values.get('GEN_VAL2')  # 前回: 2,925 (オンワラント?)
        gen_val3 = copper_values.get('GEN_VAL3')  # 確定: 56,250 (総在庫)
        gen_val4 = copper_values.get('GEN_VAL4')  # 新発見: キャンセルワラント?
        gen_val7 = copper_values.get('GEN_VAL7')  # 新発見: キャンセルワラント比率?
        
        print("構造分析:")
        if gen_val3:
            print(f"総在庫 (GEN_VAL3): {gen_val3:,} トン")
        if gen_val2:
            print(f"オンワラント推定 (GEN_VAL2): {gen_val2:,} トン")
        if gen_val4:
            print(f"キャンセルワラント推定 (GEN_VAL4): {gen_val4:,} トン")
        if gen_val1:
            print(f"未特定フィールド (GEN_VAL1): {gen_val1:,}")
        if gen_val7:
            print(f"キャンセル比率推定 (GEN_VAL7): {gen_val7}")
            
        print()
        
        # 3. 構造整合性チェック
        print("3. 構造整合性チェック:")
        print("-" * 40)
        
        if gen_val3 and gen_val4:
            # キャンセルワラント比率を計算
            calculated_ratio = (gen_val4 / gen_val3) * 100
            print(f"計算されたキャンセル比率: {calculated_ratio:.2f}%")
            
            if gen_val7:
                print(f"GEN_VAL7のキャンセル比率: {gen_val7}")
                if isinstance(gen_val7, (int, float)):
                    ratio_diff = abs(calculated_ratio - gen_val7)
                    print(f"差異: {ratio_diff:.2f}%")
                    if ratio_diff < 1:
                        print("✅ GEN_VAL7はキャンセル比率として整合性あり")
                    else:
                        print("⚠️  GEN_VAL7とキャンセル比率に差異あり")
        
        if gen_val2 and gen_val3 and gen_val4:
            # オンワラント = 総在庫 - キャンセルワラント の検証
            calculated_on_warrant = gen_val3 - gen_val4
            print(f"計算されたオンワラント (総在庫-キャンセル): {calculated_on_warrant:,}")
            print(f"GEN_VAL2 (推定オンワラント): {gen_val2:,}")
            
            if abs(calculated_on_warrant - gen_val2) < 100:  # 100トン以内の誤差
                print("✅ GEN_VAL2はオンワラントとして整合性あり")
            else:
                print("⚠️  計算値とGEN_VAL2に差異あり")
        
        print()
        
        # 4. ワラント分析
        print("4. ワラント市場分析:")
        print("-" * 40)
        
        if gen_val3 and gen_val4:
            cancel_ratio = (gen_val4 / gen_val3) * 100
            on_warrant_est = gen_val3 - gen_val4
            
            print(f"総在庫: {gen_val3:,} トン")
            print(f"キャンセルワラント: {gen_val4:,} トン ({cancel_ratio:.1f}%)")
            print(f"残存オンワラント: {on_warrant_est:,} トン ({100-cancel_ratio:.1f}%)")
            print()
            
            # 市場含意
            if cancel_ratio > 20:
                print("🔥 市場含意: 極めて高いキャンセル率 → 強いバックワーデーション圧力")
                print("   現物需要が非常に強く、現物プレミアム拡大の可能性")
            elif cancel_ratio > 10:
                print("📈 市場含意: 高いキャンセル率 → バックワーデーション傾向")
                print("   現物需要が堅調、近限月プレミアム")
            elif cancel_ratio > 5:
                print("📊 市場含意: 中程度キャンセル率 → 中立的市場")
                print("   需給バランス、正常なCarry Cost")
            else:
                print("📉 市場含意: 低いキャンセル率 → コンタンゴ傾向")
                print("   供給過剰気味、遠限月プレミアム")

    # 5. 他のフィールドとの比較
    print("\n5. 関連フィールドとの比較:")
    print("-" * 40)
    
    try:
        # 基本的な在庫フィールドも取得
        basic_fields = ['CF_LAST', 'CF_CLOSE', 'CLOSE', 'VALUE']
        basic_data, basic_err = ek.get_data(copper_ric, basic_fields)
        
        if not basic_data.empty:
            basic_row = basic_data.iloc[0]
            print("基本フィールド:")
            for field in basic_fields:
                value = basic_row.get(field)
                if pd.notna(value) and value is not None:
                    print(f"  {field}: {value}")
        
        # 0#LME-STOCKSチェーンとの比較
        print("\n総在庫の他ソースとの比較:")
        chain_data, chain_err = ek.get_data("0#LME-STOCKS", ['CF_LAST', 'CF_NAME'])
        if not chain_data.empty:
            for _, row in chain_data.iterrows():
                name = row.get('CF_NAME', '')
                value = row.get('CF_LAST')
                if 'COPPER' in str(name).upper() and pd.notna(value):
                    print(f"  {name}: {value:,}")
                    if gen_val3 and abs(value - gen_val3) < 1000:
                        print(f"    ✅ GEN_VAL3 ({gen_val3:,}) と整合性あり")
    
    except Exception as e:
        print(f"比較データ取得エラー: {e}")
    
    # 6. まとめ
    print(f"\n6. 発見されたワラント構造まとめ:")
    print("=" * 60)
    print("銅 (MCUSTX-TOTAL) フィールドマッピング:")
    print("  GEN_VAL1: [要調査] - 未特定")  
    print("  GEN_VAL2: オンワラント (公式倉庫在庫)")
    print("  GEN_VAL3: 総在庫 (確定)")
    print("  GEN_VAL4: キャンセルワラント (ユーザー発見)")
    print("  GEN_VAL7: キャンセルワラント比率 (ユーザー発見)")
    print()
    print("この構造が正しければ、全LME金属で同様のパターンが期待される")

if __name__ == "__main__":
    test_copper_detailed_warrants()