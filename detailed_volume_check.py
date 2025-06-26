#!/usr/bin/env python3
"""
修正後の詳細な出来高トレンド確認
"""

import eikon as ek
from lme_daily_report import LMEReportGenerator
import logging

def detailed_volume_check():
    """修正後の詳細確認"""
    try:
        # デバッグログを有効化
        logging.basicConfig(level=logging.DEBUG)
        
        generator = LMEReportGenerator()
        
        # 銅の詳細トレンド
        print("修正後の銅出来高トレンド詳細:")
        print("=" * 50)
        
        ric = "CMCU3"
        current_volume = 21365  # 前営業日(6/24)の出来高
        
        trend_result = generator._get_volume_trend(ric, current_volume=current_volume)
        
        print(f"トレンド結果:")
        print(f"  最新出来高: {trend_result.get('latest_volume'):,} 契約")
        print(f"  過去平均: {trend_result.get('avg_volume'):,} 契約")
        print(f"  平均比: {trend_result.get('vs_average_pct'):+.1f}%")
        print(f"  活動度: {trend_result.get('activity_level')}")
        print(f"  データ点数: {trend_result.get('data_points')}")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    detailed_volume_check()