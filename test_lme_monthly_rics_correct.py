#!/usr/bin/env python3
"""
LME月次契約RIC正確パターンテスト - MCCU+月コード+西暦
"""

import json
import eikon as ek
import pandas as pd
from datetime import datetime, timedelta

def load_config():
    """設定ファイル読み込み"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

def test_lme_monthly_ric_pattern():
    """LME月次契約RIC正確パターンテスト"""
    
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
    
    # 月コード対応表
    month_codes = {
        1: 'F',   # January
        2: 'G',   # February  
        3: 'H',   # March
        4: 'J',   # April
        5: 'K',   # May
        6: 'M',   # June
        7: 'N',   # July
        8: 'Q',   # August
        9: 'U',   # September
        10: 'V',  # October
        11: 'X',  # November
        12: 'Z'   # December
    }
    
    # 現在から6ヶ月先まで
    current_date = datetime.now()
    
    print("=" * 80)
    print("LME月次契約RIC正確パターンテスト - MCCU+月コード+西暦")
    print("=" * 80)
    
    working_rics = {}
    results = {}
    
    for i in range(1, 7):  # 第1〜第6限月
        target_date = current_date + timedelta(days=30 * i)  # 約i月後
        month = target_date.month
        year = target_date.year
        
        month_code = month_codes[month]
        year_code = str(year)[-2:]  # 西暦下2桁
        
        # RIC生成: MCCU + 月コード + 西暦下2桁
        ric = f"MCCU{month_code}{year_code}"
        contract_name = f"LME銅先物第{i}限月"
        
        print(f"\n【第{i}限月 - {target_date.strftime('%Y年%m月')}】")
        print(f"  RIC: {ric}")
        print(f"  月コード: {month_code}")
        print(f"  年コード: {year_code}")
        
        try:
            # 基本データ取得テスト
            fields = ['CF_LAST', 'CF_DATE', 'CF_CLOSE', 'CF_VOLUME', 'CF_HIGH', 'CF_LOW']
            data, err = ek.get_data(ric, fields)
            
            if data is not None and not data.empty:
                row = data.iloc[0]
                last_price = row.get('CF_LAST')
                last_date = row.get('CF_DATE')
                close_price = row.get('CF_CLOSE')
                volume = row.get('CF_VOLUME')
                high_price = row.get('CF_HIGH')
                low_price = row.get('CF_LOW')
                
                if pd.notna(last_price) and last_price is not None:
                    print(f"  ✓ 最新価格: ${last_price:,.2f}/MT")
                    print(f"  ✓ 日付: {last_date}")
                    
                    # 価格詳細
                    if pd.notna(close_price):
                        print(f"  ✓ 終値: ${close_price:,.2f}/MT")
                    if pd.notna(high_price) and pd.notna(low_price):
                        print(f"  ✓ 高値: ${high_price:,.2f}, 安値: ${low_price:,.2f}")
                    
                    # 出来高
                    if pd.notna(volume) and volume is not None:
                        print(f"  ✓ 出来高: {volume:,.0f} 契約")
                        liquidity = "高流動性" if volume > 1000 else "中流動性" if volume > 100 else "低流動性"
                        print(f"  ✓ 流動性: {liquidity}")
                    else:
                        liquidity = "不明"
                        print(f"  ⚠ 出来高: データなし")
                    
                    # 結果記録
                    working_rics[f"{i}m"] = {
                        'ric': ric,
                        'name': contract_name,
                        'maturity_months': i,
                        'target_month': month,
                        'target_year': year,
                        'month_code': month_code,
                        'year_code': year_code,
                        'price': last_price,
                        'volume': volume if pd.notna(volume) else 0,
                        'liquidity': liquidity,
                        'date': str(last_date)
                    }
                    
                    results[ric] = True
                    print(f"  → 評価: 成功")
                    
                else:
                    print(f"  ✗ 有効な価格データなし")
                    results[ric] = False
            else:
                print(f"  ✗ データ取得失敗")
                results[ric] = False
            
            if err:
                print(f"  警告: {err}")
                
        except Exception as e:
            print(f"  ✗ RICエラー: {e}")
            results[ric] = False
    
    # 結果分析
    print("\n" + "=" * 80)
    print("LME月次契約RIC正確パターンテスト結果")
    print("=" * 80)
    
    success_count = len(working_rics)
    total_count = 6
    
    print(f"\n✓ 有効契約: {success_count}/{total_count}")
    
    if working_rics:
        print(f"\n有効RIC一覧:")
        for period, info in working_rics.items():
            print(f"  {period}: {info['ric']} - {info['name']}")
            print(f"    価格: ${info['price']:,.2f}/MT")
            print(f"    出来高: {info.get('volume', 0):,.0f} 契約")
            print(f"    流動性: {info['liquidity']}")
            print()
        
        # config.json更新案
        print(f"💡 config.json更新案:")
        print(f'"lme": {{')
        print(f'  "exchange_name": "London Metal Exchange",')
        print(f'  "currency": "USD",')
        print(f'  "unit": "MT",')
        print(f'  "contracts": {{')
        
        for period in ['1m', '2m', '3m', '4m', '5m', '6m']:
            if period in working_rics:
                info = working_rics[period]
                ric = info['ric']
                name = info['name']
                maturity_months = info['maturity_months']
                liquidity = "high" if info['liquidity'] == "高流動性" else "medium" if info['liquidity'] == "中流動性" else "low"
                
                print(f'    "{period}": {{')
                print(f'      "ric": "{ric}",')
                print(f'      "name": "{name}",')
                print(f'      "maturity_months": {maturity_months},')
                print(f'      "liquidity_tier": "{liquidity}"')
                print(f'    }},')
        
        print(f'  }}')
        print(f'}}')
        
        # 期間構造分析
        if len(working_rics) >= 2:
            print(f"\n📈 期間構造分析:")
            sorted_contracts = sorted(working_rics.items(), key=lambda x: x[1]['maturity_months'])
            
            for period, info in sorted_contracts:
                print(f"  第{info['maturity_months']}限月 ({info['target_year']}-{info['target_month']:02d}): ${info['price']:,.2f}/MT")
            
            # フロント vs バック価格差
            if len(sorted_contracts) >= 2:
                front_price = sorted_contracts[0][1]['price']
                back_price = sorted_contracts[-1][1]['price']
                price_diff = back_price - front_price
                front_months = sorted_contracts[0][1]['maturity_months']
                back_months = sorted_contracts[-1][1]['maturity_months']
                months_diff = back_months - front_months
                
                if months_diff > 0:
                    monthly_slope = price_diff / months_diff
                    
                    print(f"\n  期間構造:")
                    print(f"    第{front_months}限月 vs 第{back_months}限月: {price_diff:+,.2f} USD/MT")
                    print(f"    月間スロープ: {monthly_slope:+.2f} USD/MT/月")
                    
                    if price_diff > 50:
                        structure = "コンタンゴ"
                    elif price_diff < -50:
                        structure = "バックワーデーション"
                    else:
                        structure = "フラット"
                    
                    print(f"    構造タイプ: {structure}")
    
    return working_rics, results

if __name__ == "__main__":
    try:
        working, results = test_lme_monthly_ric_pattern()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")