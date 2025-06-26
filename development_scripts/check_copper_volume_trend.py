#!/usr/bin/env python3
"""
銅の出来高トレンドを詳細確認
"""

import eikon as ek
from lme_daily_report import LMEReportGenerator
from datetime import datetime, timedelta

def check_copper_volume_detail():
    """銅の出来高詳細確認"""
    try:
        generator = LMEReportGenerator()
        
        # 過去10日間のデータを取得
        previous_business_day = generator._get_previous_business_day()
        start_date = previous_business_day - timedelta(days=15)
        
        print(f"銅(CMCU3)の出来高トレンド詳細確認")
        print(f"前営業日: {previous_business_day.strftime('%Y-%m-%d')}")
        print(f"取得期間: {start_date.strftime('%Y-%m-%d')} ～ {previous_business_day.strftime('%Y-%m-%d')}")
        
        ts_data = ek.get_timeseries(
            "CMCU3",
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=previous_business_day.strftime('%Y-%m-%d'),
            fields=['VOLUME']
        )
        
        if ts_data is not None and not ts_data.empty:
            print(f"\n取得データ:")
            for date, row in ts_data.iterrows():
                volume = row['VOLUME']
                if not pd.isna(volume):
                    print(f"  {date.strftime('%Y-%m-%d')}: {volume:,.0f} 契約")
            
            # 最新5営業日
            recent_5 = ts_data.tail(5)
            print(f"\n最新5営業日:")
            volumes = []
            for date, row in recent_5.iterrows():
                volume = row['VOLUME']
                if not pd.isna(volume):
                    volumes.append(volume)
                    print(f"  {date.strftime('%Y-%m-%d')}: {volume:,.0f} 契約")
            
            if len(volumes) >= 5:
                latest = volumes[-1]  # 最新日 (6/24)
                previous_4_avg = sum(volumes[:-1]) / len(volumes[:-1])  # 過去4日平均
                all_5_avg = sum(volumes) / len(volumes)  # 全5日平均
                
                print(f"\n計算結果:")
                print(f"  最新日(6/24): {latest:,.0f} 契約")
                print(f"  過去4日平均: {previous_4_avg:,.0f} 契約")
                print(f"  全5日平均: {all_5_avg:,.0f} 契約")
                print(f"  vs 過去4日平均: {((latest - previous_4_avg) / previous_4_avg * 100):+.1f}%")
                print(f"  vs 全5日平均: {((latest - all_5_avg) / all_5_avg * 100):+.1f}%")
                
                # 前日比較
                if len(volumes) >= 2:
                    previous_day = volumes[-2]
                    day_change = ((latest - previous_day) / previous_day * 100)
                    print(f"  前営業日比: {day_change:+.1f}% ({latest:,.0f} vs {previous_day:,.0f})")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    import pandas as pd
    check_copper_volume_detail()