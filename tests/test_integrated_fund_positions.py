#!/usr/bin/env python3
"""
統合されたファンドポジション機能の動作確認テスト
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lme_daily_report import LMEReportGenerator

def test_integrated_fund_positions():
    """統合されたファンドポジション機能テスト"""
    
    print("=" * 70)
    print("LME Daily Report - 統合ファンドポジション機能テスト")
    print("=" * 70)
    
    try:
        # LMEReportGeneratorインスタンス生成
        generator = LMEReportGenerator()
        print("✓ LMEReportGenerator初期化成功")
        
        # ファンドポジション機能単独テスト
        print("\n【ファンドポジションデータ取得テスト】")
        fund_data = generator.get_fund_position_data()
        
        if fund_data:
            print(f"✓ ファンドポジションデータ取得成功: {len(fund_data)} 金属")
            
            for metal, data in fund_data.items():
                if isinstance(data, dict):
                    long_pos = data.get('long_position', 'N/A')
                    short_pos = data.get('short_position', 'N/A')
                    net_pos = data.get('net_position', 'N/A')
                    sentiment = data.get('sentiment', 'N/A')
                    
                    print(f"  {metal}:")
                    print(f"    ロング: {long_pos:,.0f} 契約" if isinstance(long_pos, (int, float)) else f"    ロング: {long_pos}")
                    print(f"    ショート: {short_pos:,.0f} 契約" if isinstance(short_pos, (int, float)) else f"    ショート: {short_pos}")
                    if isinstance(net_pos, (int, float)):
                        print(f"    ネット: {net_pos:+,.0f} 契約 ({sentiment})")
                    else:
                        print(f"    ネット: {net_pos} ({sentiment})")
                else:
                    print(f"  {metal}: データ形式エラー")
                    
        else:
            print("✗ ファンドポジションデータ取得失敗")
            return False
        
        # フォーマット機能テスト
        print(f"\n【ファンドポジションフォーマットテスト】")
        formatted_output = generator._format_fund_position_data(fund_data)
        
        if formatted_output and "投資ファンドポジションデータ取得エラー" not in formatted_output:
            print("✓ フォーマット機能成功")
            print("\n--- フォーマット出力サンプル ---")
            print(formatted_output[:800] + "..." if len(formatted_output) > 800 else formatted_output)
        else:
            print("✗ フォーマット機能失敗")
            return False
        
        # 簡易統合テスト（レポート生成なし、データ収集のみ）
        print(f"\n【統合テスト（データ収集）】")
        try:
            # 主要データ収集テスト
            test_data = {
                'prices': generator.get_price_data(),
                'inventory': generator.get_inventory_data(),
                'fund_positions': fund_data,  # 既に取得済み
                'volume': generator.get_volume_data()
            }
            
            successful_sections = 0
            for section, data in test_data.items():
                if data:
                    successful_sections += 1
                    print(f"  ✓ {section}: 成功")
                else:
                    print(f"  ✗ {section}: 失敗")
            
            if successful_sections >= 3:  # 4セクション中3つ以上成功すればOK
                print(f"✓ 統合テスト成功 ({successful_sections}/4 セクション)")
            else:
                print(f"✗ 統合テスト失敗 ({successful_sections}/4 セクション)")
                return False
                
        except Exception as integration_error:
            print(f"✗ 統合テストエラー: {integration_error}")
            return False
        
        print(f"\n" + "=" * 70)
        print("統合ファンドポジション機能テスト結果: 成功")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"✗ テスト実行エラー: {e}")
        print(f"\n" + "=" * 70)
        print("統合ファンドポジション機能テスト結果: 失敗")
        print("=" * 70)
        return False

if __name__ == "__main__":
    try:
        success = test_integrated_fund_positions()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)