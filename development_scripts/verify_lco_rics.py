#!/usr/bin/env python3
"""
LCOc1とLCOc3の詳細検証
"""

import eikon as ek
from lme_daily_report import LMEReportGenerator

def verify_lco_rics():
    """LCOc1とLCOc3を詳細検証"""
    try:
        generator = LMEReportGenerator()
        
        # Bloomberg値との比較
        bloomberg_data = {
            "2025-06-23": 39315,
            "2025-06-20": 50860, 
            "2025-06-19": 33214,
            "2025-06-18": 40402
        }
        
        print("=== LCOc1 vs LCOc3 vs Bloomberg比較 ===")
        print("日付        Bloomberg    CMCU3       LCOc1        LCOc3        LCOc3/10")
        print("-" * 80)
        
        for date, bloomberg_vol in bloomberg_data.items():
            # CMCU3（現在）
            try:
                cmcu3_data = ek.get_timeseries("CMCU3", start_date=date, end_date=date, fields=['VOLUME'])
                cmcu3_vol = cmcu3_data['VOLUME'].iloc[0] if not cmcu3_data.empty else 0
            except:
                cmcu3_vol = 0
            
            # LCOc1
            try:
                lcoc1_data = ek.get_timeseries("LCOc1", start_date=date, end_date=date, fields=['VOLUME'])
                lcoc1_vol = lcoc1_data['VOLUME'].iloc[0] if not lcoc1_data.empty else 0
            except:
                lcoc1_vol = 0
            
            # LCOc3  
            try:
                lcoc3_data = ek.get_timeseries("LCOc3", start_date=date, end_date=date, fields=['VOLUME'])
                lcoc3_vol = lcoc3_data['VOLUME'].iloc[0] if not lcoc3_data.empty else 0
            except:
                lcoc3_vol = 0
            
            # LCOc3を10で割った値
            lcoc3_div10 = lcoc3_vol / 10 if lcoc3_vol > 0 else 0
            
            print(f"{date}  {bloomberg_vol:8,}  {cmcu3_vol:8,.0f}  {lcoc1_vol:10,.0f}  {lcoc3_vol:10,.0f}  {lcoc3_div10:8,.0f}")
        
        # LCOc3の詳細情報取得
        print(f"\n=== LCOc3 詳細情報 ===")
        try:
            # 基本情報
            df, err = ek.get_data("LCOc3", ['CF_NAME', 'LONGNAME', 'CURRENCY', 'CF_LAST', 'PCTCHNG'])
            if not df.empty:
                print(f"名称: {df.get('CF_NAME', ['N/A']).iloc[0]}")
                print(f"正式名: {df.get('LONGNAME', ['N/A']).iloc[0]}")
                print(f"通貨: {df.get('CURRENCY', ['N/A']).iloc[0]}")
                print(f"最終価格: {df.get('CF_LAST', ['N/A']).iloc[0]}")
            
            if err:
                print(f"警告: {err}")
                
        except Exception as e:
            print(f"詳細情報取得エラー: {e}")
        
        # 過去1週間のLCOc3データ
        print(f"\n=== LCOc3 過去1週間の出来高 ===")
        try:
            week_data = ek.get_timeseries("LCOc3", start_date="2025-06-16", end_date="2025-06-24", fields=['VOLUME'])
            if not week_data.empty:
                for date, row in week_data.iterrows():
                    volume = row['VOLUME']
                    volume_div10 = volume / 10
                    print(f"  {date.strftime('%Y-%m-%d')}: {volume:10,.0f} → {volume_div10:8,.0f} (÷10)")
        except Exception as e:
            print(f"週間データエラー: {e}")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    verify_lco_rics()