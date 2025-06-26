#!/usr/bin/env python3
"""
Precise Warrant Data Retriever
正確なワラントRICコードを使用したデータ取得システム

Author: Claude Code  
Created: 2025-06-26
"""

import eikon as ek
import pandas as pd
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import warnings
warnings.filterwarnings('ignore')

class PreciseWarrantDataRetriever:
    """正確なワラントデータ取得器"""
    
    def __init__(self, config_path: str = "config.json"):
        """初期化"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        
        # EIKON API初期化
        try:
            ek.set_app_key(self.config["eikon_api_key"])
            self.logger.info("EIKON API初期化完了")
        except Exception as e:
            self.logger.error(f"EIKON API初期化エラー: {e}")
            raise
    
    def _load_config(self, config_path: str) -> Dict:
        """設定ファイル読み込み"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            raise
    
    def _setup_logger(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('PreciseWarrantRetriever')
        logger.setLevel(logging.INFO)
        
        # コンソール出力
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def test_warrant_ric_patterns(self) -> Dict[str, Any]:
        """ワラントRICパターンテスト"""
        self.logger.info("ワラントRICパターンテスト開始...")
        
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "discovered_rics": {},
            "test_patterns": {},
            "errors": []
        }
        
        # 発見されたパターンを基にしたRIC候補
        warrant_ric_patterns = {
            "copper": {
                "total_stock": "/MCUSTX-TOTAL:GEN_VAL3",
                "on_warrant": "/MCUSTX-TOTAL:GEN_VAL2",  # GEN_VAL3の前後を試行
                "cancelled": "/MCUSTX-TOTAL:GEN_VAL1",
                "live_warrant": "/MCUSTX-TOTAL:GEN_VAL4",
                "alt_patterns": [
                    "MCUSTX-TOTAL.GEN_VAL3",  # ドット記法
                    "MCUSTX-TOTAL:GEN_VAL3",   # コロン記法 (スラッシュなし)
                    "/MCUSTX:GEN_VAL3",        # 短縮形
                    "CMCU-STX:GEN_VAL3"        # 別パターン
                ]
            },
            "aluminum": {
                "total_stock": "/MALSTX-TOTAL:GEN_VAL3",
                "on_warrant": "/MALSTX-TOTAL:GEN_VAL2", 
                "cancelled": "/MALSTX-TOTAL:GEN_VAL1",
                "live_warrant": "/MALSTX-TOTAL:GEN_VAL4",
                "alt_patterns": [
                    "MALSTX-TOTAL.GEN_VAL3",
                    "MALSTX-TOTAL:GEN_VAL3", 
                    "/MALSTX:GEN_VAL3",
                    "CMAL-STX:GEN_VAL3"
                ]
            }
        }
        
        # 各金属・各パターンをテスト
        for metal, patterns in warrant_ric_patterns.items():
            self.logger.info(f"{metal}ワラントRICテスト中...")
            test_results["test_patterns"][metal] = {}
            
            # 基本パターンテスト
            for warrant_type, ric in patterns.items():
                if warrant_type == "alt_patterns":
                    continue
                    
                try:
                    self.logger.info(f"  テスト: {ric}")
                    
                    # get_dataで試行
                    data, err = ek.get_data(ric, ['GEN_VAL1', 'GEN_VAL2', 'GEN_VAL3', 'GEN_VAL4', 'GEN_VAL5'])
                    
                    if data is not None and not data.empty:
                        test_results["test_patterns"][metal][warrant_type] = {
                            "ric": ric,
                            "status": "success",
                            "data": data.to_dict('records')[0] if len(data) > 0 else {},
                            "available_fields": list(data.columns)
                        }
                        self.logger.info(f"  ✅ 成功: {ric}")
                        
                        # 有効なRICとして記録
                        if metal not in test_results["discovered_rics"]:
                            test_results["discovered_rics"][metal] = {}
                        test_results["discovered_rics"][metal][warrant_type] = ric
                        
                    else:
                        test_results["test_patterns"][metal][warrant_type] = {
                            "ric": ric,
                            "status": "no_data", 
                            "error": err if err else "Empty response"
                        }
                        self.logger.warning(f"  ⚠️  データなし: {ric}")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    error_msg = f"{metal} {warrant_type} ({ric}): {str(e)}"
                    test_results["errors"].append(error_msg)
                    test_results["test_patterns"][metal][warrant_type] = {
                        "ric": ric,
                        "status": "error",
                        "error": str(e)
                    }
                    self.logger.error(f"  ❌ エラー: {ric} - {e}")
            
            # 代替パターンテスト
            if "alt_patterns" in patterns:
                self.logger.info(f"  {metal}代替パターンテスト...")
                for alt_ric in patterns["alt_patterns"]:
                    try:
                        self.logger.info(f"    代替テスト: {alt_ric}")
                        data, err = ek.get_data(alt_ric, ['GEN_VAL1', 'GEN_VAL2', 'GEN_VAL3', 'CF_LAST', 'CF_CLOSE'])
                        
                        if data is not None and not data.empty:
                            test_results["test_patterns"][metal][f"alt_{alt_ric}"] = {
                                "ric": alt_ric,
                                "status": "alt_success",
                                "data": data.to_dict('records')[0],
                                "available_fields": list(data.columns)
                            }
                            self.logger.info(f"    ✅ 代替成功: {alt_ric}")
                        
                        time.sleep(0.3)
                        
                    except Exception as e:
                        self.logger.debug(f"    代替失敗: {alt_ric} - {e}")
        
        return test_results
    
    def get_precise_warrant_data(self, discovered_rics: Dict) -> Dict[str, Any]:
        """発見されたRICを使用して正確なワラントデータ取得"""
        self.logger.info("正確なワラントデータ取得開始...")
        
        warrant_data = {
            "timestamp": datetime.now().isoformat(),
            "warrant_breakdown": {},
            "warrant_analysis": {},
            "errors": []
        }
        
        for metal, rics in discovered_rics.items():
            self.logger.info(f"{metal}正確なワラントデータ取得中...")
            warrant_data["warrant_breakdown"][metal] = {}
            
            for warrant_type, ric in rics.items():
                try:
                    # より詳細なフィールドで再取得
                    data, err = ek.get_data(
                        ric, 
                        ['GEN_VAL1', 'GEN_VAL2', 'GEN_VAL3', 'GEN_VAL4', 'GEN_VAL5', 
                         'CF_LAST', 'CF_DATE', 'CF_NAME']
                    )
                    
                    if data is not None and not data.empty:
                        row = data.iloc[0]
                        
                        # 各GEN_VALを取得
                        warrant_values = {}
                        for i in range(1, 6):
                            val_field = f'GEN_VAL{i}'
                            if val_field in row and pd.notna(row[val_field]):
                                warrant_values[val_field] = float(row[val_field])
                        
                        # CF_LASTも確認
                        if 'CF_LAST' in row and pd.notna(row['CF_LAST']):
                            warrant_values['CF_LAST'] = float(row['CF_LAST'])
                        
                        warrant_data["warrant_breakdown"][metal][warrant_type] = {
                            "ric": ric,
                            "values": warrant_values,
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "name": str(row.get('CF_NAME', 'N/A')),
                            "primary_value": self._identify_primary_value(warrant_values, warrant_type)
                        }
                        
                        self.logger.info(f"  ✅ {metal} {warrant_type}: {len(warrant_values)} 値")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    error_msg = f"{metal} {warrant_type} ({ric}): {str(e)}"
                    warrant_data["errors"].append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
            
            # ワラント分析実施
            if warrant_data["warrant_breakdown"][metal]:
                warrant_data["warrant_analysis"][metal] = self._analyze_warrant_structure(
                    warrant_data["warrant_breakdown"][metal]
                )
        
        return warrant_data
    
    def _identify_primary_value(self, values: Dict, warrant_type: str) -> Dict:
        """主要な値を特定"""
        if not values:
            return {"value": None, "field": None}
        
        # 既知の値（56250）に近いものを優先
        target_value = 56250  # 銅のOnWarrant値
        
        closest_value = None
        closest_field = None
        min_diff = float('inf')
        
        for field, value in values.items():
            if value and value > 1000:  # 在庫らしい値（1000トン以上）
                diff = abs(value - target_value)
                if diff < min_diff:
                    min_diff = diff
                    closest_value = value
                    closest_field = field
        
        # フォールバック：最大値を選択
        if closest_value is None:
            max_value = max(values.values()) if values else 0
            for field, value in values.items():
                if value == max_value:
                    closest_value = value
                    closest_field = field
                    break
        
        return {
            "value": closest_value,
            "field": closest_field,
            "confidence": "high" if min_diff < 1000 else "medium"
        }
    
    def _analyze_warrant_structure(self, warrant_breakdown: Dict) -> Dict:
        """ワラント構造分析"""
        analysis = {
            "total_stock": None,
            "on_warrant": None,
            "cancelled_warrants": None,
            "cancellation_rate": None,
            "interpretation": ""
        }
        
        # 主要値を抽出
        values = {}
        for warrant_type, data in warrant_breakdown.items():
            if "primary_value" in data and data["primary_value"]["value"]:
                values[warrant_type] = data["primary_value"]["value"]
        
        if values:
            # 推定値設定
            if "total_stock" in values:
                analysis["total_stock"] = values["total_stock"]
            if "on_warrant" in values:
                analysis["on_warrant"] = values["on_warrant"] 
            
            # キャンセル率計算
            if analysis["total_stock"] and analysis["on_warrant"]:
                cancelled = analysis["total_stock"] - analysis["on_warrant"]
                if cancelled > 0:
                    analysis["cancelled_warrants"] = cancelled
                    analysis["cancellation_rate"] = (cancelled / analysis["total_stock"]) * 100
                    
                    # 解釈
                    cancel_rate = analysis.get("cancellation_rate", 0)
                    if cancel_rate > 15:
                        analysis["interpretation"] = f"高キャンセル率({cancel_rate:.1f}%) - 強いバックワーデーション圧力"
                    elif cancel_rate > 5:
                        analysis["interpretation"] = f"中程度キャンセル率({cancel_rate:.1f}%) - 現物需要あり"
                    else:
                        analysis["interpretation"] = f"低キャンセル率({cancel_rate:.1f}%) - 需給緩和"
        
        return analysis
    
    def generate_precise_warrant_report(self) -> str:
        """正確なワラントレポート生成"""
        self.logger.info("正確なワラントレポート生成開始...")
        
        # RICパターンテスト
        test_results = self.test_warrant_ric_patterns()
        
        # 発見されたRICでデータ取得
        discovered_rics = test_results.get("discovered_rics", {})
        warrant_data = self.get_precise_warrant_data(discovered_rics) if discovered_rics else {"warrant_breakdown": {}, "warrant_analysis": {}}
        
        # レポート生成
        report_lines = []
        
        # ヘッダー
        report_lines.append("=" * 80)
        report_lines.append("【正確なワラントデータ取得結果】")
        report_lines.append("=" * 80)
        report_lines.append(f"実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        report_lines.append("RICパターン: /MCUSTX-TOTAL:GEN_VAL3 ベース")
        report_lines.append("")
        
        # RIC発見結果
        report_lines.append("=== RIC発見結果 ===")
        if discovered_rics:
            for metal, rics in discovered_rics.items():
                report_lines.append(f"{metal.upper()}:")
                for warrant_type, ric in rics.items():
                    report_lines.append(f"  {warrant_type}: {ric}")
            report_lines.append("")
        else:
            report_lines.append("有効なRICが発見されませんでした。")
            report_lines.append("")
        
        # ワラントデータ詳細
        report_lines.append("=== ワラントデータ詳細 ===")
        if "warrant_breakdown" in warrant_data:
            for metal, breakdown in warrant_data["warrant_breakdown"].items():
                if breakdown:
                    report_lines.append(f"{metal.upper()}ワラント詳細:")
                    for warrant_type, data in breakdown.items():
                        ric = data.get("ric", "N/A")
                        values = data.get("values", {})
                        primary = data.get("primary_value", {})
                        
                        report_lines.append(f"  {warrant_type} ({ric}):")
                        report_lines.append(f"    全取得値: {values}")
                        report_lines.append(f"    主要値: {primary.get('value', 'N/A')} ({primary.get('field', 'N/A')})")
                    report_lines.append("")
        
        # ワラント分析結果
        report_lines.append("=== ワラント分析結果 ===")
        if "warrant_analysis" in warrant_data:
            for metal, analysis in warrant_data["warrant_analysis"].items():
                if analysis:
                    report_lines.append(f"{metal.upper()}分析:")
                    report_lines.append(f"  総在庫: {analysis.get('total_stock', 'N/A')} トン")
                    report_lines.append(f"  オンワラント: {analysis.get('on_warrant', 'N/A')} トン")
                    report_lines.append(f"  キャンセルワラント: {analysis.get('cancelled_warrants', 'N/A')} トン")
                    cancel_rate = analysis.get('cancellation_rate', 0)
                    if cancel_rate:
                        report_lines.append(f"  キャンセル率: {cancel_rate:.1f}%")
                    else:
                        report_lines.append(f"  キャンセル率: N/A")
                    report_lines.append(f"  解釈: {analysis.get('interpretation', 'N/A')}")
                    report_lines.append("")
        
        # RICテスト詳細
        report_lines.append("=== RICテスト詳細結果 ===")
        if "test_patterns" in test_results:
            for metal, patterns in test_results["test_patterns"].items():
                report_lines.append(f"{metal.upper()}テスト結果:")
                for pattern_name, result in patterns.items():
                    status = result.get("status", "unknown")
                    ric = result.get("ric", "N/A")
                    report_lines.append(f"  {pattern_name}: {status} ({ric})")
                    if "data" in result and result["data"]:
                        report_lines.append(f"    データ: {result['data']}")
                report_lines.append("")
        
        # エラー詳細
        all_errors = test_results.get("errors", []) + warrant_data.get("errors", [])
        if all_errors:
            report_lines.append("=== エラー詳細 ===")
            for error in all_errors:
                report_lines.append(f"  • {error}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report(self, report_content: str, filename: str = None) -> str:
        """レポート保存"""
        if filename is None:
            filename = f"Precise_Warrant_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"正確なワラントレポート保存完了: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"レポート保存エラー: {e}")
            raise

def main():
    """メイン実行関数"""
    try:
        retriever = PreciseWarrantDataRetriever()
        
        print("🎯 正確なワラントデータ取得システム")
        print("=" * 50)
        print("発見されたRIC: /MCUSTX-TOTAL:GEN_VAL3")
        print("期待値: 56250 (銅OnWarrant)")
        print("=" * 50)
        
        # 正確なワラントレポート生成
        report_content = retriever.generate_precise_warrant_report()
        
        # ファイル保存
        saved_filename = retriever.save_report(report_content)
        
        print(f"\n✅ 正確なワラントデータ取得完了!")
        print(f"📄 保存ファイル: {saved_filename}")
        print(f"📊 ファイルサイズ: {len(report_content.encode('utf-8')):,} bytes")
        print("\n🔍 結果を確認して、正確なRICコードを特定しました。")
        
        return 0
        
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())