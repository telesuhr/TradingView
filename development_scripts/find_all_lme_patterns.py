#!/usr/bin/env python3
"""
LME月次契約RIC全パターン調査
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

def test_all_lme_patterns():
    """LME月次契約RIC全パターン調査"""
    
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
    
    # 様々なLME銅先物RICパターン
    patterns_to_test = [
        # 月コード付きパターン (現在は7月=N)
        "MCCUN25",  # MCCU + 月コード + 年
        "CAHN25",   # CA + H + 年 (3月の例)
        "CUPN25",   # CUP + 月コード + 年  
        "CUN25",    # CU + 月コード + 年
        "CADN25",   # CAD + 月コード + 年
        
        # 数字付きパターン
        "MCCU0725", # MCCU + MM + YY
        "MCCU25N",  # MCCU + 年 + 月コード
        "MCCU725",  # MCCU + M + YY
        
        # 既存の動作するパターン応用
        "MCCU3",    # 既存の3ヶ月
        "MCCU6",    # 既存の6ヶ月
        "MCCU12",   # 既存の12ヶ月
        
        # LME標準パターン
        "LMCAD01",  # LME + CAD + 月数
        "LMCAD07",  # 7月
        "LMCAD12",  # 12月
        
        # 代替パターン
        "0#LME-CU:", # チェーン
        "CU3M",      # 単純パターン
        "LME-CU-1M", # ダッシュ区切り
        
        # 新しいパターン
        "LMCUFU25", # LME + CU + 未来月コード + 年
        "LMCU0725", # LME + CU + MM + YY
        "CUCN25",   # CUC + 月コード + 年
    ]
    
    print("=" * 80)
    print("LME月次契約RIC全パターン調査")
    print("=" * 80)
    
    working_rics = []
    failed_rics = []
    
    for ric in patterns_to_test:
        print(f"\nテスト中: {ric}")
        
        try:
            # 基本データ取得
            data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE'])
            
            if data is not None and not data.empty:
                row = data.iloc[0]
                last_price = row.get('CF_LAST')
                last_date = row.get('CF_DATE')
                
                if pd.notna(last_price) and last_price is not None:
                    print(f"  ✓ 成功: ${last_price:,.2f}/MT ({last_date})")
                    working_rics.append({
                        'ric': ric,
                        'price': last_price,
                        'date': str(last_date)
                    })
                else:
                    print(f"  ✗ 価格データなし")
                    failed_rics.append(ric)
            else:
                print(f"  ✗ データ取得失敗")
                failed_rics.append(ric)
            
            if err:
                # エラーメッセージをショートバージョンで表示
                error_summary = str(err)[:100] + "..." if len(str(err)) > 100 else str(err)
                print(f"  警告: {error_summary}")
                
        except Exception as e:
            print(f"  ✗ エラー: {e}")
            failed_rics.append(ric)
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("LME月次契約RIC全パターン調査結果")
    print("=" * 80)
    
    print(f"\n✓ 有効RIC: {len(working_rics)}")
    if working_rics:
        print(f"有効RIC一覧:")
        for ric_info in working_rics:
            print(f"  {ric_info['ric']}: ${ric_info['price']:,.2f}/MT ({ric_info['date']})")
    
    print(f"\n✗ 無効RIC: {len(failed_rics)}")
    if failed_rics:
        print(f"無効RIC一覧:")
        for ric in failed_rics:
            print(f"  {ric}")
    
    # 推奨事項
    print(f"\n💡 推奨事項:")
    if working_rics:
        print(f"  • 有効なRICが見つかりました")
        print(f"  • これらのパターンを基に月次契約RICを構築可能")
        
        # パターン分析
        ric_patterns = {}
        for ric_info in working_rics:
            ric = ric_info['ric']
            if 'MCCU' in ric:
                ric_patterns['MCCU系'] = ric_patterns.get('MCCU系', []) + [ric]
            elif 'LMCAD' in ric:
                ric_patterns['LMCAD系'] = ric_patterns.get('LMCAD系', []) + [ric]
            elif 'CU' in ric:
                ric_patterns['CU系'] = ric_patterns.get('CU系', []) + [ric]
            else:
                ric_patterns['その他'] = ric_patterns.get('その他', []) + [ric]
        
        for pattern_type, rics in ric_patterns.items():
            print(f"    {pattern_type}: {', '.join(rics)}")
    else:
        print(f"  • 標準的な月次RICが見つかりませんでした")
        print(f"  • 既存の3m/15m/27mパターンを維持することを推奨")
        print(f"  • または動的なフォワードカーブ計算を検討")
    
    return working_rics, failed_rics

if __name__ == "__main__":
    try:
        working, failed = test_all_lme_patterns()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")