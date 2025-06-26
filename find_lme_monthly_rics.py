#!/usr/bin/env python3
"""
LME月間RIC調査 - 第1〜第6限月の正しいRICを発見
"""

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

def test_lme_ric_variants():
    """LME月間RIC候補テスト"""
    
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
    
    # LME銅月間RIC候補
    lme_ric_candidates = {
        "現在使用中": {
            "cash": "LMCAD00",
            "3m": "CMCU3",
            "15m": "CMCU15",
            "27m": "CMCU27"
        },
        "月間固定RIC": {
            "1m": "CMCU1",
            "2m": "CMCU2",
            "4m": "CMCU4", 
            "5m": "CMCU5",
            "6m": "CMCU6"
        },
        "代替RIC_1": {
            "cash": "LMCADS00",
            "1m": "LMCAD01",
            "2m": "LMCAD02",
            "3m": "LMCAD03",
            "4m": "LMCAD04",
            "5m": "LMCAD05",
            "6m": "LMCAD06"
        },
        "代替RIC_2": {
            "cash": "CU-CASH",
            "1m": "CU-1M",
            "2m": "CU-2M",
            "3m": "CU-3M", 
            "4m": "CU-4M",
            "5m": "CU-5M",
            "6m": "CU-6M"
        },
        "代替RIC_3": {
            "cash": "LMCUCASH",
            "1m": "LMCU1M",
            "2m": "LMCU2M",
            "3m": "LMCU3M",
            "4m": "LMCU4M",
            "5m": "LMCU5M",
            "6m": "LMCU6M"
        },
        "代替RIC_4": {
            "cash": "LME-CU-CASH",
            "1m": "LME-CU-1M",
            "2m": "LME-CU-2M", 
            "3m": "LME-CU-3M",
            "4m": "LME-CU-4M",
            "5m": "LME-CU-5M",
            "6m": "LME-CU-6M"
        }
    }
    
    print("=" * 80)
    print("LME月間RIC調査 - 第1〜第6限月の正しいRICを発見")
    print("=" * 80)
    
    working_rics = {}
    all_results = {}
    
    for category, rics in lme_ric_candidates.items():
        print(f"\n【{category}】")
        
        for period, ric in rics.items():
            print(f"  {period}: {ric}")
            
            try:
                # 基本データ取得テスト
                fields = ['CF_LAST', 'CF_DATE', 'CF_CLOSE']
                data, err = ek.get_data(ric, fields)
                
                if data is not None and not data.empty:
                    row = data.iloc[0]
                    last_price = row.get('CF_LAST')
                    last_date = row.get('CF_DATE')
                    close_price = row.get('CF_CLOSE')
                    
                    if pd.notna(last_price) and last_price is not None:
                        print(f"    ✓ 価格: ${last_price:,.2f}/MT 日付: {last_date}")
                        working_rics[period] = {
                            'ric': ric,
                            'price': last_price,
                            'date': str(last_date),
                            'category': category
                        }
                        all_results[f"{category}_{period}"] = True
                    else:
                        print(f"    ✗ 価格データなし")
                        all_results[f"{category}_{period}"] = False
                else:
                    print(f"    ✗ データ取得失敗")
                    all_results[f"{category}_{period}"] = False
                
                if err:
                    print(f"    警告: {err}")
                    
            except Exception as e:
                print(f"    ✗ エラー: {e}")
                all_results[f"{category}_{period}"] = False
    
    # 結果分析
    print("\n" + "=" * 80)
    print("LME月間RIC調査結果")
    print("=" * 80)
    
    if working_rics:
        print(f"\n✓ 動作するRIC: {len(working_rics)} 個")
        print(f"\n動作するRIC一覧:")
        for period, info in working_rics.items():
            print(f"  {period}: {info['ric']} (${info['price']:,.2f}/MT) [{info['category']}]")
        
        # 最適なRIC組み合わせを提案
        print(f"\n📊 推奨RIC組み合わせ:")
        
        # 期間別に最良のRICを選択
        periods_needed = ['cash', '1m', '2m', '3m', '4m', '5m', '6m']
        recommended_rics = {}
        
        for period in periods_needed:
            if period in working_rics:
                recommended_rics[period] = working_rics[period]
        
        if recommended_rics:
            print(f"  利用可能期間: {len(recommended_rics)}/{len(periods_needed)}")
            for period, info in recommended_rics.items():
                print(f"    {period}: {info['ric']} (${info['price']:,.2f}/MT)")
        
        # config.json更新案
        if len(recommended_rics) >= 4:  # 最低4つの期間があれば
            print(f"\n💡 config.json更新案:")
            print(f'  "lme": {{')
            print(f'    "exchange_name": "London Metal Exchange",')
            print(f'    "currency": "USD",')
            print(f'    "unit": "MT",')
            print(f'    "contracts": {{')
            
            for period in periods_needed:
                if period in recommended_rics:
                    info = recommended_rics[period]
                    ric = info['ric']
                    price = info['price']
                    month_num = 0 if period == 'cash' else int(period[:-1])
                    
                    if period == 'cash':
                        name = "LME銅現金決済"
                    else:
                        name = f"LME銅{month_num}ヶ月"
                    
                    print(f'      "{period}": {{')
                    print(f'        "ric": "{ric}",')
                    print(f'        "name": "{name}",')
                    print(f'        "maturity_months": {month_num},')
                    print(f'        "liquidity_tier": "high"')
                    print(f'      }},')
            
            print(f'    }}')
            print(f'  }}')
    else:
        print(f"\n✗ 動作するRICが見つかりませんでした")
        
        # 代替策の提案
        print(f"\n💡 代替策:")
        print(f"  1. 既存のforward_curve_ricsを使用")
        print(f"  2. get_timeseries()で動的に期間を計算")
        print(f"  3. 他のLME期間RICパターンを調査")
    
    return working_rics, all_results

if __name__ == "__main__":
    try:
        working, results = test_lme_ric_variants()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")