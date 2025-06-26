#!/usr/bin/env python3
"""
異なるRICや方法での出来高比較
"""

import eikon as ek
from lme_daily_report import LMEReportGenerator
import pandas as pd

def compare_volume_methods():
    """異なる方法での出来高比較"""
    try:
        generator = LMEReportGenerator()
        
        # 6/23と6/24の比較
        dates = ['2025-06-23', '2025-06-24']
        
        print("出来高データ比較検証")
        print("=" * 50)
        
        for date in dates:
            print(f"\n【{date}】")
            
            # 方法1: CMCU3 (3ヶ月先物)
            try:
                ts_data = ek.get_timeseries(
                    "CMCU3",
                    start_date=date,
                    end_date=date,
                    interval='daily',
                    fields=['VOLUME']
                )
                volume_3m = ts_data['VOLUME'].iloc[0] if not ts_data.empty else None
                print(f"  CMCU3 (3ヶ月): {volume_3m:,.0f} 契約" if volume_3m else "  CMCU3: データなし")
            except Exception as e:
                print(f"  CMCU3: エラー - {e}")
            
            # 方法2: CF_VOLUME フィールドで確認
            try:
                df, err = ek.get_data("CMCU3", ['CF_VOLUME'])
                if not df.empty and 'CF_VOLUME' in df.columns:
                    cf_volume = df['CF_VOLUME'].iloc[0]
                    print(f"  CF_VOLUME: {cf_volume:,.0f} 契約" if cf_volume else "  CF_VOLUME: データなし")
                if err:
                    print(f"  CF_VOLUME警告: {err}")
            except Exception as e:
                print(f"  CF_VOLUME: エラー - {e}")
                
            # 方法3: 他の出来高フィールド
            try:
                df2, err2 = ek.get_data("CMCU3", ['ACVOL_UNS', 'TURNOVER'])
                if not df2.empty:
                    for field in ['ACVOL_UNS', 'TURNOVER']:
                        if field in df2.columns:
                            value = df2[field].iloc[0]
                            print(f"  {field}: {value:,.0f}" if value and not pd.isna(value) else f"  {field}: データなし")
                if err2:
                    print(f"  その他フィールド警告: {err2}")
            except Exception as e:
                print(f"  その他フィールド: エラー - {e}")
        
        # 前営業日取得ロジックでの再確認
        print(f"\n【前営業日ロジック再実行】")
        volume_data = generator.get_volume_data()
        if 'Copper' in volume_data:
            copper_data = volume_data['Copper']
            print(f"  現在のロジック結果: {copper_data.get('volume'):,.0f} 契約")
            trend = copper_data.get('trend', {})
            if trend:
                print(f"  トレンド - 平均: {trend.get('avg_volume'):,.0f}, 比較: {trend.get('vs_average_pct'):+.1f}%")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    compare_volume_methods()