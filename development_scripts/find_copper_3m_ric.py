#!/usr/bin/env python3
"""
正しい銅3M先物RICの特定
"""

import eikon as ek

def find_copper_3m_ric():
    """正しい銅3M先物RICを特定"""
    try:
        # 一般的なLME銅RICパターン
        copper_patterns = [
            # LME Official patterns
            "LMCADS03",   # LME Copper 3M Official
            "LME-CU-3M",  # LME Copper 3M Alternative
            "LMCU3M",     # LME Copper 3M
            "LMCU=",      # LME Copper Generic
            
            # CME/Comex patterns
            "HGc1",       # Copper Futures Active Contract
            "HGc3",       # Copper Futures 3rd Month
            "HG3M=",      # Copper 3M
            
            # European patterns  
            "CU3M=",      # Copper 3M Generic
            "CUc3",       # Copper 3rd Contract
            "LCAc3",      # LCA Copper 3rd
            
            # Alternative LME patterns
            "CMCAH3",     # Copper Mar 2025
            "CMCAM3",     # Copper Jun 2025  
            "CMCAN3",     # Copper Jul 2025
            
            # Bloomberg Terminal patterns (Eikon equivalent)
            "LME/CU3M",   # LME Copper 3M
            "LMEH3",      # LME Copper Mar
            
            # Other common patterns
            "CAH25",      # Copper Mar 2025
            "CAM25",      # Copper Jun 2025
            "CAN25",      # Copper Jul 2025
        ]
        
        target_date = "2025-06-23"
        bloomberg_target = 39315
        
        print("=== 銅3M先物RIC候補検索 ===")
        print(f"目標日: {target_date}")
        print(f"Bloomberg目標値: {bloomberg_target:,} 契約")
        print("-" * 60)
        
        successful_rics = []
        
        for ric in copper_patterns:
            try:
                # 価格データで銅かどうか確認
                price_data = ek.get_timeseries(ric, start_date=target_date, end_date=target_date, fields=['CLOSE'])
                volume_data = ek.get_timeseries(ric, start_date=target_date, end_date=target_date, fields=['VOLUME'])
                
                if not price_data.empty and not volume_data.empty:
                    price = price_data['CLOSE'].iloc[0] if 'CLOSE' in price_data.columns else None
                    volume = volume_data['VOLUME'].iloc[0] if 'VOLUME' in volume_data.columns else None
                    
                    # 銅価格の妥当性チェック（$8000-$12000程度）
                    is_copper_price = price and 8000 <= price <= 12000
                    
                    # Bloomberg値との近さ
                    volume_ratio = volume / bloomberg_target if volume and bloomberg_target > 0 else 0
                    
                    print(f"{ric:<12} | 価格: ${price:8.2f} | 出来高: {volume:10,.0f} | 比率: {volume_ratio:5.2f} | 銅?: {is_copper_price}")
                    
                    if is_copper_price and 0.5 <= volume_ratio <= 2.0:
                        successful_rics.append((ric, volume, volume_ratio))
                
            except Exception as e:
                print(f"{ric:<12} | エラー: {str(e)[:40]}...")
        
        # 成功したRICの詳細確認
        if successful_rics:
            print(f"\n=== 有望な候補RIC ===")
            for ric, volume, ratio in successful_rics:
                print(f"{ric}: {volume:,.0f} 契約 (Bloomberg比 {ratio:.2f})")
                
                # 複数日での検証
                print(f"  過去5日間の出来高:")
                try:
                    multi_day = ek.get_timeseries(ric, start_date="2025-06-18", end_date="2025-06-24", fields=['VOLUME'])
                    if not multi_day.empty:
                        for date, row in multi_day.iterrows():
                            vol = row['VOLUME']
                            print(f"    {date.strftime('%Y-%m-%d')}: {vol:8,.0f}")
                except:
                    print(f"    複数日データ取得失敗")
        
        # 全てのLME契約を検索
        print(f"\n=== LME契約チェーン検索 ===")
        try:
            # LME Copper契約チェーン
            chain_patterns = ["0#LME-CU:", "0#CMCU:", "0#CU-LME:"]
            for pattern in chain_patterns:
                try:
                    chain_data = ek.get_data(pattern, ['CF_NAME'])
                    if not chain_data.empty:
                        print(f"{pattern}: {len(chain_data)} 契約見つかりました")
                        for i, name in enumerate(chain_data['CF_NAME'].head(10)):
                            print(f"  {i+1}. {name}")
                except:
                    print(f"{pattern}: アクセス不可")
        except Exception as e:
            print(f"チェーン検索エラー: {e}")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    find_copper_3m_ric()