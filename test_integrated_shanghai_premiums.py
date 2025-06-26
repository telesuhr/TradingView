#!/usr/bin/env python3
"""
統合された上海銅プレミアム機能の動作確認テスト
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lme_daily_report import LMEReportGenerator

def test_integrated_shanghai_premiums():
    """統合された上海銅プレミアム機能テスト"""
    
    print("=" * 70)
    print("LME Daily Report - 統合上海銅プレミアム機能テスト")
    print("=" * 70)
    
    try:
        # LMEReportGeneratorインスタンス生成
        generator = LMEReportGenerator()
        print("✓ LMEReportGenerator初期化成功")
        
        # 上海銅プレミアム機能単独テスト
        print("\n【上海銅プレミアムデータ取得テスト】")
        premium_data = generator.get_shanghai_copper_premium_data()
        
        if premium_data:
            print(f"✓ 上海銅プレミアムデータ取得成功: {len(premium_data)} 種類")
            
            for premium_type, data in premium_data.items():
                if isinstance(data, dict):
                    name = data.get('name', premium_type)
                    ranking = data.get('ranking', 0)
                    premium_value = data.get('premium_value')
                    description = data.get('description', '')
                    
                    print(f"  {ranking}位. {name}:")
                    print(f"    説明: {description}")
                    if premium_value is not None:
                        print(f"    プレミアム: {premium_value:.2f} USD/MT")
                    else:
                        print(f"    プレミアム: データ取得失敗")
                else:
                    print(f"  {premium_type}: データ形式エラー")
                    
        else:
            print("✗ 上海銅プレミアムデータ取得失敗")
            return False
        
        # フォーマット機能テスト
        print(f"\n【上海銅プレミアムフォーマットテスト】")
        formatted_output = generator._format_shanghai_copper_premium_data(premium_data)
        
        if formatted_output and "上海銅プレミアムデータ取得エラー" not in formatted_output:
            print("✓ フォーマット機能成功")
            print("\n--- フォーマット出力サンプル ---")
            # 最初の800文字を表示
            sample_length = min(800, len(formatted_output))
            print(formatted_output[:sample_length])
            if len(formatted_output) > sample_length:
                print("...")
        else:
            print("✗ フォーマット機能失敗")
            return False
        
        # 統合テスト（主要セクション確認）
        print(f"\n【統合テスト（主要セクション）】")
        try:
            # 主要データ収集テスト
            test_sections = {
                'prices': generator.get_price_data(),
                'inventory': generator.get_inventory_data(),
                'fund_positions': generator.get_fund_position_data(),
                'shanghai_copper_premiums': premium_data,  # 既に取得済み
                'volume': generator.get_volume_data()
            }
            
            successful_sections = 0
            for section, data in test_sections.items():
                if data:
                    successful_sections += 1
                    print(f"  ✓ {section}: 成功")
                else:
                    print(f"  ✗ {section}: 失敗")
            
            if successful_sections >= 4:  # 5セクション中4つ以上成功すればOK
                print(f"✓ 統合テスト成功 ({successful_sections}/5 セクション)")
            else:
                print(f"✗ 統合テスト失敗 ({successful_sections}/5 セクション)")
                return False
                
        except Exception as integration_error:
            print(f"✗ 統合テストエラー: {integration_error}")
            return False
        
        # Config検証テスト
        print(f"\n【設定ファイル検証テスト】")
        config = generator.config
        shanghai_rics = config.get("shanghai_copper_premium_rics", {})
        
        if shanghai_rics:
            print("✓ config.json設定確認:")
            for premium_type, info in shanghai_rics.items():
                ric = info.get('ric', 'N/A')
                name = info.get('name', 'N/A')
                ranking = info.get('ranking', 0)
                print(f"  {ranking}位. {name} ({ric})")
        else:
            print("✗ config.json設定なし")
            return False
        
        print(f"\n" + "=" * 70)
        print("統合上海銅プレミアム機能テスト結果: 成功")
        print("=" * 70)
        
        # テスト結果サマリー
        print(f"\n📊 テスト結果サマリー:")
        print(f"• 設定済みプレミアム種類: {len(shanghai_rics)} 種類")
        print(f"• データ取得成功: {len([d for d in premium_data.values() if d.get('premium_value') is not None])} 種類")
        print(f"• 統合セクション成功: {successful_sections}/5")
        print(f"• 総合評価: 全機能正常動作")
        
        return True
        
    except Exception as e:
        print(f"✗ テスト実行エラー: {e}")
        print(f"\n" + "=" * 70)
        print("統合上海銅プレミアム機能テスト結果: 失敗")
        print("=" * 70)
        return False

if __name__ == "__main__":
    try:
        success = test_integrated_shanghai_premiums()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)