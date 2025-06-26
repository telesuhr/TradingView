#!/usr/bin/env python3
"""
正しい銅3M先物出来高の特定
"""

import eikon as ek
from lme_daily_report import LMEReportGenerator
import pandas as pd

def find_correct_copper_volume():
    """正しい銅3M先物出来高を特定"""
    try:
        generator = LMEReportGenerator()
        
        # 6/23の検証（Bloomberg: 39,315）
        target_date = "2025-06-23"
        print(f"=== {target_date} 銅出来高検証 ===")
        print(f"Bloomberg期待値: 39,315契約")
        
        # 1. 異なるRICを試す
        copper_rics = [
            "CMCU3",      # 現在使用中
            "CMCU0",      # Cash/Spot
            "CMCU1",      # 1M
            "CMCU2",      # 2M  
            "LCOc1",      # 別の3M表記
            "LCOc3",      # 別の3M表記
            "LCAU3",      # LME Official 3M
            "0#LCO:",     # 全銅先物チェーン
        ]
        
        print(f"\n--- 異なるRICでの出来高 ---")
        for ric in copper_rics:
            try:
                ts_data = ek.get_timeseries(
                    ric,
                    start_date=target_date,
                    end_date=target_date,
                    interval='daily',
                    fields=['VOLUME']
                )
                
                if ts_data is not None and not ts_data.empty and 'VOLUME' in ts_data.columns:
                    volume = ts_data['VOLUME'].iloc[0]
                    print(f"  {ric}: {volume:,.0f} 契約")
                else:
                    print(f"  {ric}: データなし")
                    
            except Exception as e:
                print(f"  {ric}: エラー - {e}")
        
        # 2. 異なるフィールドを試す
        print(f"\n--- CMCU3での異なるフィールド ---")
        volume_fields = [
            'VOLUME',      # 現在使用
            'VOL',         # 短縮形
            'ACVOL_UNS',   # 累積出来高
            'CF_VOLUME',   # Close Volume
            'TURNOVER',    # 売買代金
            'TOTAL_VOLUME',# 合計出来高
            'NUM_TRADES',  # 取引回数
        ]
        
        for field in volume_fields:
            try:
                ts_data = ek.get_timeseries(
                    "CMCU3",
                    start_date=target_date,
                    end_date=target_date,
                    interval='daily',
                    fields=[field]
                )
                
                if ts_data is not None and not ts_data.empty and field in ts_data.columns:
                    value = ts_data[field].iloc[0]
                    print(f"  {field}: {value:,.0f}")
                else:
                    print(f"  {field}: データなし")
                    
            except Exception as e:
                print(f"  {field}: エラー - {e}")
        
        # 3. get_dataで利用可能なフィールドを確認
        print(f"\n--- get_dataで利用可能な出来高フィールド ---")
        try:
            # よく使われる出来高関連フィールド
            data_fields = [
                'CF_VOLUME', 'VOL', 'ACVOL_UNS', 'ACVOL_1', 
                'TOTAL_VOL', 'TOT_TURNOVER', 'TURNOVER'
            ]
            
            df, err = ek.get_data("CMCU3", data_fields)
            if err:
                print(f"  警告: {err}")
            
            if not df.empty:
                for field in data_fields:
                    if field in df.columns:
                        value = df[field].iloc[0]
                        if value and not pd.isna(value):
                            print(f"  {field}: {value:,.0f}")
                        else:
                            print(f"  {field}: null/NA")
                            
        except Exception as e:
            print(f"  get_dataエラー: {e}")
        
        # 4. LME公式の可能性があるRIC
        print(f"\n--- LME公式系RIC ---")
        lme_official_rics = [
            "LCAU3",      # LME Copper 3M Official
            "LCA3M=",     # LME Copper 3M
            "CUAH3",      # LME Copper 3M Alternative
            "LMECUc3",    # LME Copper 3M
        ]
        
        for ric in lme_official_rics:
            try:
                ts_data = ek.get_timeseries(
                    ric,
                    start_date=target_date,
                    end_date=target_date,
                    interval='daily',
                    fields=['VOLUME']
                )
                
                if ts_data is not None and not ts_data.empty:
                    volume = ts_data['VOLUME'].iloc[0] if 'VOLUME' in ts_data.columns else 'N/A'
                    print(f"  {ric}: {volume}")
                    
            except Exception as e:
                print(f"  {ric}: エラー - {e}")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    find_correct_copper_volume()