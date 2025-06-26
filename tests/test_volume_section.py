#!/usr/bin/env python3
"""
Test volume section generation with fixed trend calculation
"""

from lme_daily_report import LMEReportGenerator

def test_volume_section():
    """Test volume section generation"""
    try:
        # Initialize the report generator
        generator = LMEReportGenerator()
        
        # Get volume data
        print("Getting volume data...")
        volume_data = generator.get_volume_data()
        
        print("\nVolume data results:")
        for metal, data in volume_data.items():
            if data and 'volume' in data and 'trend' in data:
                trend = data['trend']
                volume = data['volume']
                print(f"\n【{metal}】")
                print(f"  出来高: {volume:,} 契約" if volume else "  出来高: データなし")
                if trend:
                    activity = trend.get('activity_level', 'データなし')
                    vs_avg = trend.get('vs_average_pct', 'データなし')
                    print(f"    (活動度: {activity}、平均比 {vs_avg:+.1f}%)" if vs_avg != 'データなし' else f"    (活動度: {activity})")
        
    except Exception as e:
        print(f"Error testing volume section: {e}")

if __name__ == "__main__":
    test_volume_section()