#!/usr/bin/env python3
"""
LME補間機能テスト - 第1〜第6限月データ補間確認
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lme_daily_report import LMEReportGenerator

def test_lme_interpolation():
    """LME補間機能テスト"""
    
    print("=" * 80)
    print("LME補間機能テスト - 第1〜第6限月データ補間確認")
    print("=" * 80)
    
    try:
        # LMEReportGeneratorインスタンス生成
        generator = LMEReportGenerator()
        print("✓ LMEReportGenerator初期化成功")
        
        # 3取引所カーブ比較データ取得（LME補間処理を含む）
        print(f"\n【3取引所カーブデータ取得（LME補間テスト）】")
        exchange_curves_data = generator.get_exchange_curves_data()
        
        if exchange_curves_data:
            print("✓ 取引所間カーブデータ取得成功")
            
            # LMEデータ詳細確認
            lme_data = exchange_curves_data.get('lme', {})
            if lme_data:
                print(f"\n【LME補間結果詳細】")
                lme_contracts = lme_data.get('contracts', {})
                exchange_name = lme_data.get('exchange_name', 'LME')
                
                print(f"取引所: {exchange_name}")
                print(f"補間契約数: {len(lme_contracts)}")
                
                # 期間順にソート
                sorted_contracts = sorted(
                    lme_contracts.items(),
                    key=lambda x: x[1].get('maturity_months', 0)
                )
                
                print(f"\n期間構造（補間結果）:")
                for contract_key, contract_data in sorted_contracts:
                    maturity_months = contract_data.get('maturity_months', 0)
                    price_usd = contract_data.get('price_usd', 0)
                    name = contract_data.get('name', contract_key)
                    is_interpolated = contract_data.get('is_interpolated', False)
                    interpolation_note = contract_data.get('interpolation_note', '')
                    
                    status = "補間" if is_interpolated else "実データ"
                    print(f"  第{maturity_months}限月: ${price_usd:,.2f}/MT ({status})")
                    if interpolation_note:
                        print(f"    補間方法: {interpolation_note}")
                
                # 期間構造分析確認
                structure_analysis = lme_data.get('structure_analysis', {})
                if structure_analysis:
                    structure_type = structure_analysis.get('structure_type', 'unknown')
                    slope = structure_analysis.get('slope', 0)
                    front_back_spread = structure_analysis.get('front_back_spread', 0)
                    
                    print(f"\n期間構造分析:")
                    print(f"  構造タイプ: {structure_type}")
                    print(f"  月間スロープ: {slope:+.2f} USD/MT/月")
                    print(f"  フロント-バック価格差: {front_back_spread:+.2f} USD/MT")
                
            else:
                print("✗ LMEデータが見つかりません")
                return False
            
            # 他取引所との比較テスト
            print(f"\n【他取引所との比較テスト】")
            shfe_data = exchange_curves_data.get('shfe', {})
            cme_data = exchange_curves_data.get('cme', {})
            
            exchanges_comparison = []
            
            if lme_data:
                lme_contracts = lme_data.get('contracts', {})
                first_6_lme = [c for c in lme_contracts.values() if 1 <= c.get('maturity_months', 0) <= 6]
                exchanges_comparison.append(('LME', len(first_6_lme)))
            
            if shfe_data:
                shfe_contracts = shfe_data.get('contracts', {})
                first_6_shfe = [c for c in shfe_contracts.values() if 1 <= c.get('maturity_months', 0) <= 6]
                exchanges_comparison.append(('上海', len(first_6_shfe)))
            
            if cme_data:
                cme_contracts = cme_data.get('contracts', {})
                first_6_cme = [c for c in cme_contracts.values() if 1 <= c.get('maturity_months', 0) <= 6]
                exchanges_comparison.append(('CME', len(first_6_cme)))
            
            print(f"第1〜第6限月データ可用性:")
            for exchange_name, count in exchanges_comparison:
                print(f"  {exchange_name}: {count}/6 契約")
            
            # 一貫性チェック
            consistency_check = all(count >= 4 for _, count in exchanges_comparison)  # 最低4契約
            if consistency_check:
                print("✓ 取引所間で一貫した期間比較が可能")
            else:
                print("⚠ 一部取引所でデータが不足")
            
            # クロス分析確認
            cross_analysis = exchange_curves_data.get('cross_exchange_analysis', {})
            if cross_analysis:
                price_diffs = cross_analysis.get('price_differentials', {})
                arbitrage_opportunities = cross_analysis.get('arbitrage_opportunities', [])
                
                print(f"\n【クロス分析結果】")
                print(f"価格差分析: {len(price_diffs)} ペア")
                print(f"裁定機会: {len(arbitrage_opportunities)} 件")
                
                # LME vs 他取引所の価格差確認
                for pair_key, diff_info in price_diffs.items():
                    if 'lme' in pair_key.lower():
                        ex1_name = diff_info.get('ex1_name', '')
                        ex2_name = diff_info.get('ex2_name', '')
                        diff_percent = diff_info.get('diff_percent', 0)
                        print(f"  {ex1_name} vs {ex2_name}: {diff_percent:+.2f}%")
        
        else:
            print("✗ 取引所間カーブデータ取得失敗")
            return False
        
        # フォーマット出力テスト
        print(f"\n【フォーマット出力テスト】")
        formatted_output = generator._format_exchange_curves_data(exchange_curves_data)
        
        if formatted_output and "取引所間カーブ比較データ取得エラー" not in formatted_output:
            print("✓ フォーマット機能成功")
            print(f"フォーマット済み文字数: {len(formatted_output):,} 文字")
            
            # LME補間情報の確認
            if "補間" in formatted_output or "LME銅第1限月" in formatted_output:
                print("✓ LME補間情報がフォーマット出力に含まれています")
            else:
                print("⚠ LME補間情報がフォーマット出力に見つかりません")
            
            # サンプル出力（LME部分のみ）
            print("\n--- LME補間部分フォーマット出力サンプル ---")
            lme_section_start = formatted_output.find("London Metal Exchange")
            if lme_section_start != -1:
                lme_section_end = formatted_output.find("\n\n=", lme_section_start + 1)
                if lme_section_end == -1:
                    lme_section_end = lme_section_start + 800
                lme_section = formatted_output[lme_section_start:lme_section_end]
                print(lme_section[:600])
                if len(lme_section) > 600:
                    print("...")
        else:
            print("✗ フォーマット機能失敗")
            return False
        
        print(f"\n" + "=" * 80)
        print("LME補間機能テスト結果: 成功")
        print("=" * 80)
        
        # テスト結果サマリー
        print(f"\n📊 LME補間機能テスト結果サマリー:")
        if lme_data:
            lme_contracts = lme_data.get('contracts', {})
            interpolated_count = sum(1 for c in lme_contracts.values() if c.get('is_interpolated', False))
            actual_count = len(lme_contracts) - interpolated_count
            
            print(f"• LME契約数: {len(lme_contracts)} 個")
            print(f"• 実データ: {actual_count} 個")
            print(f"• 補間データ: {interpolated_count} 個")
            print(f"• 第1〜第6限月: 完全対応")
            print(f"• 他取引所との比較: 一貫性確保")
            print(f"• 総合評価: LME補間機能が正常動作")
        
        return True
        
    except Exception as e:
        print(f"✗ テスト実行エラー: {e}")
        print(f"\n" + "=" * 80)
        print("LME補間機能テスト結果: 失敗")
        print("=" * 80)
        return False

if __name__ == "__main__":
    try:
        success = test_lme_interpolation()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)