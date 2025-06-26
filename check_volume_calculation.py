#!/usr/bin/env python3
"""
出来高計算方法の確認
"""

import eikon as ek

def check_volume_calculation():
    """出来高計算方法を確認"""
    try:
        target_date = "2025-06-23"
        bloomberg_target = 39315
        
        print("=== 出来高計算方法の確認 ===")
        print(f"目標: Bloomberg {bloomberg_target:,} vs EIKON 13,314")
        print(f"比率: {bloomberg_target / 13314:.2f}倍差")
        
        # 1. 現在のCMCU3データの詳細
        print(f"\n--- CMCU3 詳細データ ---")
        
        # 価格も含めて確認
        ts_data = ek.get_timeseries(
            "CMCU3",
            start_date=target_date,
            end_date=target_date,
            interval='daily',
            fields=['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']
        )
        
        if not ts_data.empty:
            row = ts_data.iloc[0]
            print(f"  日付: {target_date}")
            print(f"  始値: ${row.get('OPEN', 'N/A')}")
            print(f"  高値: ${row.get('HIGH', 'N/A')}")  
            print(f"  安値: ${row.get('LOW', 'N/A')}")
            print(f"  終値: ${row.get('CLOSE', 'N/A')}")
            print(f"  出来高: {row.get('VOLUME', 'N/A'):,.0f}")
        
        # 2. 複数の時間間隔で確認
        print(f"\n--- 異なる時間間隔での出来高 ---")
        intervals = ['daily', 'weekly', 'monthly']
        
        for interval in intervals:
            try:
                data = ek.get_timeseries("CMCU3", start_date=target_date, end_date=target_date, 
                                       interval=interval, fields=['VOLUME'])
                if not data.empty:
                    volume = data['VOLUME'].iloc[0]
                    print(f"  {interval}: {volume:,.0f}")
            except Exception as e:
                print(f"  {interval}: エラー - {e}")
        
        # 3. 銅価格で妥当性確認
        print(f"\n--- 銅価格妥当性確認 ---")
        try:
            price_data = ek.get_timeseries("CMCU3", start_date="2025-06-20", end_date="2025-06-24", 
                                         fields=['CLOSE'])
            if not price_data.empty:
                print("  過去5日間の終値:")
                for date, row in price_data.iterrows():
                    price = row['CLOSE']
                    print(f"    {date.strftime('%Y-%m-%d')}: ${price:,.2f}")
                    
                # 価格が銅の妥当範囲かチェック（$8000-$12000）
                avg_price = price_data['CLOSE'].mean()
                is_copper = 8000 <= avg_price <= 12000
                print(f"  平均価格: ${avg_price:,.2f}")
                print(f"  銅価格範囲: {'Yes' if is_copper else 'No'}")
        except Exception as e:
            print(f"  価格確認エラー: {e}")
        
        # 4. 仮説：単位変換の必要性
        print(f"\n--- 単位変換の可能性 ---")
        current_volume = 13314
        multipliers = [1, 2, 3, 2.95, 5, 10]  # 一般的な変換倍率
        
        for mult in multipliers:
            converted = current_volume * mult
            diff_pct = abs(converted - bloomberg_target) / bloomberg_target * 100
            print(f"  ×{mult}: {converted:,.0f} (差異: {diff_pct:.1f}%)")
        
        # Bloomberg値に最も近い倍率
        best_mult = bloomberg_target / current_volume
        print(f"  最適倍率: ×{best_mult:.2f} = {current_volume * best_mult:,.0f}")
        
        # 5. LME公式データとの比較可能性
        print(f"\n--- LME公式データ確認 ---")
        
        # 累積出来高や他のフィールドとの比較
        try:
            df, err = ek.get_data("CMCU3", ['CF_VOLUME', 'ACVOL_UNS', 'ACVOL_1'])
            if not df.empty:
                for col in df.columns:
                    if col != 'Instrument':
                        value = df[col].iloc[0]
                        if value and not pd.isna(value):
                            mult_needed = bloomberg_target / value if value > 0 else 0
                            print(f"  {col}: {value:,.0f} (×{mult_needed:.2f}倍 = {value * mult_needed:,.0f})")
            
            if err:
                print(f"  警告: {err}")
                
        except Exception as e:
            print(f"  公式データエラー: {e}")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    import pandas as pd
    check_volume_calculation()