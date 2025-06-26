#!/usr/bin/env python3
"""
3取引所統合テスト - LME・上海・CME銅先物カーブ比較
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lme_daily_report import LMEReportGenerator

def test_three_exchanges_integration():
    """3取引所統合テスト"""
    
    print("=" * 80)
    print("3取引所統合テスト - LME・上海・CME銅先物カーブ比較")
    print("=" * 80)
    
    try:
        # LMEReportGeneratorインスタンス生成
        generator = LMEReportGenerator()
        print("✓ LMEReportGenerator初期化成功")
        
        # 3取引所カーブ比較データ取得テスト
        print("\n【3取引所カーブ比較データ取得テスト】")
        exchange_curves_data = generator.get_exchange_curves_data()
        
        if exchange_curves_data:
            print(f"✓ 取引所間カーブデータ取得成功")
            
            # 取引所別データ確認
            exchanges = [k for k in exchange_curves_data.keys() if k != 'cross_exchange_analysis']
            print(f"  対応取引所: {len(exchanges)} 個")
            
            total_contracts = 0
            for exchange_code in exchanges:
                exchange_info = exchange_curves_data[exchange_code]
                exchange_name = exchange_info.get('exchange_name', exchange_code)
                successful_contracts = exchange_info.get('successful_contracts', 0)
                currency = exchange_info.get('currency', 'N/A')
                total_contracts += successful_contracts
                print(f"    {exchange_name} ({currency}): {successful_contracts} 契約")
            
            print(f"  総契約数: {total_contracts} 契約")
            
            # 取引所間比較分析確認
            cross_analysis = exchange_curves_data.get('cross_exchange_analysis', {})
            if cross_analysis:
                price_diffs = cross_analysis.get('price_differentials', {})
                arbitrage_opportunities = cross_analysis.get('arbitrage_opportunities', [])
                structure_comp = cross_analysis.get('structure_comparison', {})
                liquidity_comp = cross_analysis.get('liquidity_comparison', {})
                
                print(f"    取引所間価格差: {len(price_diffs)} ペア")
                print(f"    裁定機会: {len(arbitrage_opportunities)} 件")
                print(f"    期間構造比較: {len(structure_comp)} ペア")
                print(f"    流動性比較: {len(liquidity_comp)} ペア")
            
        else:
            print("✗ 取引所間カーブデータ取得失敗")
            return False
        
        # フォーマット機能テスト
        print(f"\n【3取引所フォーマットテスト】")
        formatted_output = generator._format_exchange_curves_data(exchange_curves_data)
        
        if formatted_output and "取引所間カーブ比較データ取得エラー" not in formatted_output:
            print("✓ フォーマット機能成功")
            print(f"  フォーマット済み文字数: {len(formatted_output):,} 文字")
            
            # サンプル出力（最初の1500文字）
            print("\n--- 3取引所フォーマット出力サンプル ---")
            sample_length = min(1500, len(formatted_output))
            print(formatted_output[:sample_length])
            if len(formatted_output) > sample_length:
                print("...")
                print(f"(省略 - 合計 {len(formatted_output):,} 文字)")
        else:
            print("✗ フォーマット機能失敗")
            return False
        
        # 価格水準比較分析
        print(f"\n【価格水準比較分析】")
        if cross_analysis and price_diffs:
            print("  3ヶ月先物価格水準:")
            for pair_key, diff_info in price_diffs.items():
                ex1_name = diff_info.get('ex1_name', '')
                ex2_name = diff_info.get('ex2_name', '')
                ex1_price = diff_info.get('ex1_price', 0)
                ex2_price = diff_info.get('ex2_price', 0)
                diff_percent = diff_info.get('diff_percent', 0)
                
                print(f"    {ex1_name}: ${ex1_price:,.2f}/MT")
                print(f"    {ex2_name}: ${ex2_price:,.2f}/MT")
                print(f"    価格差: {diff_percent:+.2f}%")
                print()
        
        # 期間構造比較
        print(f"\n【期間構造比較】")
        for exchange_code in exchanges:
            exchange_info = exchange_curves_data[exchange_code]
            exchange_name = exchange_info.get('exchange_name', exchange_code)
            structure_analysis = exchange_info.get('structure_analysis', {})
            
            if structure_analysis:
                structure_type = structure_analysis.get('structure_type', 'unknown')
                slope = structure_analysis.get('slope', 0)
                print(f"  {exchange_name}: {structure_type} ({slope:+.2f} USD/MT/月)")
        
        # 設定ファイル検証
        print(f"\n【設定ファイル検証】")
        config = generator.config
        exchange_curves_config = config.get("exchange_curves", {})
        
        if exchange_curves_config:
            print("✓ config.json設定確認:")
            for metal, exchanges_config in exchange_curves_config.items():
                print(f"  {metal}:")
                for exchange_code, exchange_info in exchanges_config.items():
                    exchange_name = exchange_info.get('exchange_name', exchange_code)
                    currency = exchange_info.get('currency', 'USD')
                    contracts = exchange_info.get('contracts', {})
                    
                    # コメントフィールドを除外して実際の契約数をカウント
                    actual_contracts = [c for c in contracts.keys() if 'comment' not in contracts]
                    contract_count = len(actual_contracts)
                    
                    price_conversion = exchange_info.get('price_conversion')
                    conv_info = ""
                    if price_conversion:
                        from_unit = price_conversion.get('from_unit', '')
                        to_unit = price_conversion.get('to_unit', '')
                        conv_info = f" (変換: {from_unit}→{to_unit})"
                    
                    print(f"    {exchange_name} ({currency}): {contract_count} 契約{conv_info}")
        else:
            print("✗ config.json設定なし")
            return False
        
        print(f"\n" + "=" * 80)
        print("3取引所統合テスト結果: 成功")
        print("=" * 80)
        
        # テスト結果サマリー
        print(f"\n📊 3取引所統合テスト結果サマリー:")
        print(f"• 対応取引所: {len(exchanges)} 個")
        print(f"• 総契約数: {total_contracts} 契約")
        print(f"• 取引所間価格差: {len(price_diffs) if 'price_diffs' in locals() else 0} ペア")
        print(f"• 裁定機会: {len(arbitrage_opportunities) if 'arbitrage_opportunities' in locals() else 0} 件")
        print(f"• フォーマット出力: {len(formatted_output):,} 文字")
        print(f"• 総合評価: 3取引所銅先物カーブ比較システムが正常動作")
        
        # 特別分析: 最大価格差とその市場含意
        if 'price_diffs' in locals() and price_diffs:
            max_diff = max(abs(diff_info['diff_percent']) for diff_info in price_diffs.values())
            max_diff_pair = max(price_diffs.items(), key=lambda x: abs(x[1]['diff_percent']))
            pair_name, diff_info = max_diff_pair
            
            print(f"\n🎯 注目ポイント:")
            print(f"• 最大価格差: {diff_info['diff_percent']:+.2f}% ({pair_name.replace('_vs_', ' vs ')})")
            if abs(diff_info['diff_percent']) > 5:
                print(f"• 市場含意: 大幅な価格差により裁定機会あり")
            else:
                print(f"• 市場含意: 価格差は正常範囲内")
        
        return True
        
    except Exception as e:
        print(f"✗ テスト実行エラー: {e}")
        print(f"\n" + "=" * 80)
        print("3取引所統合テスト結果: 失敗")
        print("=" * 80)
        return False

if __name__ == "__main__":
    try:
        success = test_three_exchanges_integration()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)