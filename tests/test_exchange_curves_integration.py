#!/usr/bin/env python3
"""
取引所間カーブ比較機能統合テスト
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lme_daily_report import LMEReportGenerator

def test_exchange_curves_integration():
    """取引所間カーブ比較機能統合テスト"""
    
    print("=" * 80)
    print("LME Daily Report - 取引所間カーブ比較機能統合テスト")
    print("=" * 80)
    
    try:
        # LMEReportGeneratorインスタンス生成
        generator = LMEReportGenerator()
        print("✓ LMEReportGenerator初期化成功")
        
        # 取引所間カーブ比較機能単独テスト
        print("\n【取引所間カーブ比較データ取得テスト】")
        exchange_curves_data = generator.get_exchange_curves_data()
        
        if exchange_curves_data:
            print(f"✓ 取引所間カーブデータ取得成功")
            
            # 取引所別データ確認
            exchanges = [k for k in exchange_curves_data.keys() if k != 'cross_exchange_analysis']
            print(f"  取得済み取引所: {len(exchanges)} 個")
            
            for exchange_code in exchanges:
                exchange_info = exchange_curves_data[exchange_code]
                exchange_name = exchange_info.get('exchange_name', exchange_code)
                successful_contracts = exchange_info.get('successful_contracts', 0)
                print(f"    {exchange_name}: {successful_contracts} 契約")
            
            # 取引所間比較分析確認
            cross_analysis = exchange_curves_data.get('cross_exchange_analysis', {})
            if cross_analysis:
                price_diffs = cross_analysis.get('price_differentials', {})
                arbitrage_opportunities = cross_analysis.get('arbitrage_opportunities', [])
                print(f"    取引所間価格差: {len(price_diffs)} ペア")
                print(f"    裁定機会: {len(arbitrage_opportunities)} 件")
            
        else:
            print("✗ 取引所間カーブデータ取得失敗")
            return False
        
        # フォーマット機能テスト
        print(f"\n【取引所間カーブ比較フォーマットテスト】")
        formatted_output = generator._format_exchange_curves_data(exchange_curves_data)
        
        if formatted_output and "取引所間カーブ比較データ取得エラー" not in formatted_output:
            print("✓ フォーマット機能成功")
            print("\n--- フォーマット出力サンプル ---")
            # 最初の1000文字を表示
            sample_length = min(1000, len(formatted_output))
            print(formatted_output[:sample_length])
            if len(formatted_output) > sample_length:
                print("...")
                print(f"(合計 {len(formatted_output)} 文字)")
        else:
            print("✗ フォーマット機能失敗")
            return False
        
        # 設定ファイル検証テスト
        print(f"\n【設定ファイル検証テスト】")
        config = generator.config
        exchange_curves_config = config.get("exchange_curves", {})
        
        if exchange_curves_config:
            print("✓ config.json設定確認:")
            for metal, exchanges in exchange_curves_config.items():
                print(f"  {metal}:")
                for exchange_code, exchange_info in exchanges.items():
                    exchange_name = exchange_info.get('exchange_name', exchange_code)
                    contracts = exchange_info.get('contracts', {})
                    contract_count = len([c for c in contracts.keys() if 'comment' not in contracts])
                    print(f"    {exchange_name}: {contract_count} 契約")
        else:
            print("✗ config.json設定なし")
            return False
        
        # 簡単な統合テスト（主要セクション確認）
        print(f"\n【統合テスト（主要セクション）】")
        try:
            # 主要データ収集テスト（軽量版）
            test_sections = {
                'prices': generator.get_price_data(),
                'fund_positions': generator.get_fund_position_data(),
                'shanghai_copper_premiums': generator.get_shanghai_copper_premium_data(),
                'exchange_curves': exchange_curves_data,  # 既に取得済み
            }
            
            successful_sections = 0
            for section, data in test_sections.items():
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
        
        print(f"\n" + "=" * 80)
        print("取引所間カーブ比較機能統合テスト結果: 成功")
        print("=" * 80)
        
        # テスト結果サマリー
        print(f"\n📊 テスト結果サマリー:")
        print(f"• 対応取引所: {len(exchanges)} 個 ({', '.join(exchanges)})")
        print(f"• 取引所間比較: {len(price_diffs) if 'price_diffs' in locals() else 0} ペア")
        print(f"• 裁定機会: {len(arbitrage_opportunities) if 'arbitrage_opportunities' in locals() else 0} 件")
        print(f"• 統合セクション成功: {successful_sections}/4")
        print(f"• 総合評価: 取引所間カーブ比較機能が正常動作")
        
        return True
        
    except Exception as e:
        print(f"✗ テスト実行エラー: {e}")
        print(f"\n" + "=" * 80)
        print("取引所間カーブ比較機能統合テスト結果: 失敗")
        print("=" * 80)
        return False

if __name__ == "__main__":
    try:
        success = test_exchange_curves_integration()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)