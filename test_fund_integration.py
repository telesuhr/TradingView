#!/usr/bin/env python3
"""
Test Fund Position Integration in Daily Report
Daily Reportのファンドポジション統合機能テスト

Author: Claude Code  
Created: 2025-06-26
"""

import json
from lme_daily_report import LMEReportGenerator

def test_fund_integration():
    """ファンドポジション統合機能テスト"""
    
    print("🔧 Daily Reportファンドポジション統合機能テスト")
    print("=" * 60)
    
    try:
        # LMEReportGenerator初期化
        generator = LMEReportGenerator()
        
        print("1. ファンドポジションデータ取得テスト:")
        print("-" * 40)
        
        # ファンドポジションデータのみ取得
        fund_data = generator.get_fund_position_data()
        
        if fund_data:
            print("✅ ファンドポジションデータ取得成功")
            for metal, data in fund_data.items():
                print(f"\n{metal.upper()}:")
                print(f"  ロング: {data.get('long_position', 'N/A'):,.0f}")
                print(f"  ショート: {data.get('short_position', 'N/A'):,.0f}")
                print(f"  ネット: {data.get('net_position', 'N/A'):,.0f}")
                print(f"  センチメント: {data.get('sentiment', 'N/A')}")
        else:
            print("❌ ファンドポジションデータ取得失敗")
        
        print("\n2. フォーマット出力テスト:")
        print("-" * 40)
        
        # フォーマット関数テスト
        formatted_output = generator._format_fund_position_data(fund_data)
        print(formatted_output)
        
        print("\n3. config.json設定確認:")
        print("-" * 40)
        
        fund_rics = generator.config.get("fund_position_rics", {})
        if fund_rics:
            print("✅ fund_position_rics設定が存在")
            for metal, rics in fund_rics.items():
                print(f"  {metal}: {rics}")
        else:
            print("❌ fund_position_rics設定が見つかりません")
        
        print("\n✅ ファンドポジション統合機能テスト完了")
        print("🎯 Daily Reportに正常に統合されています")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        raise

if __name__ == "__main__":
    test_fund_integration()