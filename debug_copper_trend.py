#!/usr/bin/env python3
"""
銅出来高の詳細デバッグ
"""

import eikon as ek
from lme_daily_report import LMEReportGenerator
from datetime import datetime, timedelta

def debug_copper_trend():
    """銅出来高の詳細デバッグ"""
    try:
        generator = LMEReportGenerator()
        
        print("=== 銅出来高詳細デバッグ ===")
        
        # 実際にコードが使用している営業日を確認
        previous_business_day = generator._get_previous_business_day()
        print(f"前営業日（基準日）: {previous_business_day.strftime('%Y-%m-%d')}")
        
        # 過去5営業日を計算（同じロジック）
        business_days = []
        current_date = previous_business_day
        
        for i in range(5):
            business_days.append(current_date)
            # 前の営業日を計算
            days_back = 1
            while days_back <= 7:
                candidate = current_date - timedelta(days=days_back)
                if candidate.weekday() < 5:  # 平日
                    current_date = candidate
                    break
                days_back += 1
        
        print(f"\n計算された過去5営業日:")
        for i, date in enumerate(business_days):
            print(f"  {i+1}. {date.strftime('%Y-%m-%d')} ({['月','火','水','木','金','土','日'][date.weekday()]})")
        
        # 実際のトレンド分析を実行
        print(f"\n=== 実際のトレンド分析結果 ===")
        trend_result = generator._get_volume_trend("CMCU3", current_volume=21365)
        
        if trend_result:
            print(f"最新出来高: {trend_result.get('latest_volume'):,} 契約")
            print(f"過去平均: {trend_result.get('avg_volume'):,} 契約")
            print(f"平均比: {trend_result.get('vs_average_pct'):+.1f}%")
            print(f"活動度: {trend_result.get('activity_level')}")
            print(f"データ点数: {trend_result.get('data_points')}")
        
        # 期間別比較
        print(f"\n=== 期間別比較 ===")
        
        # 過去1週間平均
        week_start = previous_business_day - timedelta(days=7)
        print(f"過去1週間（{week_start.strftime('%Y-%m-%d')}〜）との比較")
        
        # 過去1ヶ月平均  
        month_start = previous_business_day - timedelta(days=30)
        print(f"過去1ヶ月（{month_start.strftime('%Y-%m-%d')}〜）との比較")
        
        # より長期間のデータを取得して確認
        print(f"\n=== 過去10営業日の出来高 ===")
        extended_data = []
        check_date = previous_business_day
        
        for i in range(10):
            target_date_str = check_date.strftime('%Y-%m-%d')
            
            try:
                ts_data = ek.get_timeseries(
                    "CMCU3",
                    start_date=target_date_str,
                    end_date=target_date_str,
                    interval='daily',
                    fields=['VOLUME']
                )
                
                if ts_data is not None and not ts_data.empty and 'VOLUME' in ts_data.columns:
                    volume = ts_data['VOLUME'].iloc[0]
                    extended_data.append((check_date, volume))
                    print(f"  {target_date_str}: {volume:,} 契約")
                
                # 前の営業日を計算
                days_back = 1
                while days_back <= 7:
                    candidate = check_date - timedelta(days=days_back)
                    if candidate.weekday() < 5:
                        check_date = candidate
                        break
                    days_back += 1
                        
            except Exception as e:
                print(f"  {target_date_str}: エラー - {e}")
                break
        
        if len(extended_data) >= 5:
            # 異なる期間での平均計算
            last_5_volumes = [v for d, v in extended_data[:5]]
            last_4_volumes = [v for d, v in extended_data[1:5]]  # 最新日除く
            last_10_volumes = [v for d, v in extended_data]
            
            print(f"\n=== 平均比較 ===")
            print(f"最新日（6/24）: {extended_data[0][1]:,} 契約")
            print(f"過去4日平均: {sum(last_4_volumes)/len(last_4_volumes):.0f} 契約")
            print(f"過去5日平均: {sum(last_5_volumes)/len(last_5_volumes):.0f} 契約")
            if len(last_10_volumes) >= 10:
                print(f"過去10日平均: {sum(last_10_volumes)/len(last_10_volumes):.0f} 契約")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    debug_copper_trend()