#!/usr/bin/env python3
"""
出来高データ取得ロジックの一貫性確認
"""

import eikon as ek
from lme_daily_report import LMEReportGenerator
from datetime import datetime, timedelta
import pandas as pd

def verify_volume_consistency():
    """出来高データ取得の一貫性確認"""
    try:
        generator = LMEReportGenerator()
        ric = "CMCU3"
        
        # 過去5営業日分を個別に取得（前営業日と同じロジック）
        previous_business_day = generator._get_previous_business_day()
        print(f"検証: 銅(CMCU3)出来高データの一貫性")
        print(f"前営業日: {previous_business_day.strftime('%Y-%m-%d')}")
        
        dates_to_check = []
        current_date = previous_business_day
        for i in range(5):
            dates_to_check.append(current_date)
            # 前の営業日を計算
            days_back = 1
            while days_back <= 7:
                candidate = current_date - timedelta(days=days_back)
                if candidate.weekday() < 5:  # 平日
                    current_date = candidate
                    break
                days_back += 1
        
        print(f"\n各日付を個別取得（前営業日と同じロジック）:")
        individual_volumes = []
        
        for date in dates_to_check:
            target_date_str = date.strftime('%Y-%m-%d')
            
            # 方法1: 単日指定
            try:
                ts_data = ek.get_timeseries(
                    ric,
                    start_date=target_date_str,
                    end_date=target_date_str,
                    interval='daily',
                    fields=['VOLUME']
                )
                
                volume = None
                if ts_data is not None and not ts_data.empty and 'VOLUME' in ts_data.columns:
                    volume = ts_data['VOLUME'].iloc[0]
                
                print(f"  {target_date_str}: {volume:,.0f} 契約" if volume else f"  {target_date_str}: データなし")
                individual_volumes.append((date, volume))
                
            except Exception as e:
                print(f"  {target_date_str}: エラー - {e}")
                individual_volumes.append((date, None))
        
        # 範囲取得で比較
        print(f"\n範囲取得（現在の_get_volume_trendロジック）:")
        start_date = dates_to_check[-1] - timedelta(days=3)
        end_date = dates_to_check[0]
        
        ts_data_range = ek.get_timeseries(
            ric,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            fields=['VOLUME']
        )
        
        if ts_data_range is not None and not ts_data_range.empty:
            recent_data = ts_data_range.tail(5)
            print(f"  範囲取得結果:")
            for date, row in recent_data.iterrows():
                volume = row['VOLUME']
                if not pd.isna(volume):
                    print(f"    {date.strftime('%Y-%m-%d')}: {volume:,.0f} 契約")
        
        # 比較結果
        print(f"\n比較結果:")
        print(f"個別取得 vs 範囲取得で差異があるかチェック")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    verify_volume_consistency()