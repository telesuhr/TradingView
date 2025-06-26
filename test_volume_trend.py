#!/usr/bin/env python3
"""
Volume trend calculation test
"""

import eikon as ek
import json
from lme_daily_report import LMEReportGenerator

def test_volume_trend():
    """Test volume trend calculation"""
    try:
        # Initialize the report generator
        generator = LMEReportGenerator()
        
        # Test with Copper
        ric = "CMCU3"
        test_volume = 21365  # Previous business day volume
        
        print(f"Testing volume trend for {ric} with volume {test_volume}")
        
        # Get volume trend
        trend_result = generator._get_volume_trend(ric, current_volume=test_volume)
        
        print(f"Volume trend result: {trend_result}")
        
        if trend_result:
            print(f"Latest volume: {trend_result.get('latest_volume')}")
            print(f"Average volume: {trend_result.get('avg_volume')}")
            print(f"vs Average %: {trend_result.get('vs_average_pct')}%")
            print(f"Activity level: {trend_result.get('activity_level')}")
            print(f"Data points: {trend_result.get('data_points')}")
        
        return trend_result
        
    except Exception as e:
        print(f"Error testing volume trend: {e}")
        return None

if __name__ == "__main__":
    result = test_volume_trend()