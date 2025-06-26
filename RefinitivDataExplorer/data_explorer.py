#!/usr/bin/env python3
"""
Refinitiv Data Explorer
スプレッド予測精度向上のための主要データアクセス可能性検証システム

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

class RefinitivDataExplorer:
    """Refinitivデータ探索・検証システム"""
    
    def __init__(self, config_path: str = "config.json"):
        """初期化"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        self.results = {}
        
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
        logger = logging.getLogger('DataExplorer')
        logger.setLevel(logging.INFO)
        
        # コンソール出力
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def test_ric_access(self, ric: str, description: str = "") -> Dict[str, Any]:
        """単一RICのアクセス可能性テスト"""
        self.logger.info(f"テスト開始: {ric} ({description})")
        
        result = {
            "ric": ric,
            "description": description,
            "accessible": False,
            "data_available": False,
            "error": None,
            "sample_data": None,
            "fields_available": []
        }
        
        try:
            # 基本データ取得テスト
            data, err = ek.get_data(ric, ['CF_LAST', 'CF_NAME', 'CF_CLOSE'])
            
            if data is not None and not data.empty:
                result["accessible"] = True
                result["data_available"] = True
                result["sample_data"] = data.to_dict('records')[0] if len(data) > 0 else None
                result["fields_available"] = list(data.columns)
                self.logger.info(f"✅ アクセス成功: {ric}")
            else:
                result["accessible"] = True
                result["error"] = f"警告: {err}" if err else "データが空"
                self.logger.warning(f"⚠️  アクセス可能だがデータなし: {ric}")
                
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ アクセス失敗: {ric} - {e}")
        
        # API制限対策
        time.sleep(self.config.get("test_settings", {}).get("delay_between_calls", 1.0))
        
        return result
    
    def test_timeseries_access(self, ric: str, description: str = "") -> Dict[str, Any]:
        """時系列データアクセステスト"""
        self.logger.info(f"時系列テスト: {ric} ({description})")
        
        result = {
            "ric": ric,
            "description": description,
            "timeseries_available": False,
            "date_range": None,
            "sample_points": 0,
            "error": None
        }
        
        try:
            # 過去1週間のデータを試行
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            ts_data = ek.get_timeseries(
                ric,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                fields=['CLOSE', 'VOLUME']
            )
            
            if ts_data is not None and not ts_data.empty:
                result["timeseries_available"] = True
                result["date_range"] = f"{ts_data.index[0]} to {ts_data.index[-1]}"
                result["sample_points"] = len(ts_data)
                self.logger.info(f"✅ 時系列データ取得成功: {ric} ({len(ts_data)}ポイント)")
            else:
                result["error"] = "時系列データが空"
                self.logger.warning(f"⚠️  時系列データなし: {ric}")
                
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ 時系列取得失敗: {ric} - {e}")
        
        time.sleep(self.config.get("test_settings", {}).get("delay_between_calls", 1.0))
        return result
    
    def test_news_search(self, keywords: List[str], description: str = "") -> Dict[str, Any]:
        """ニュース検索テスト"""
        self.logger.info(f"ニュース検索テスト: {keywords} ({description})")
        
        result = {
            "keywords": keywords,
            "description": description,
            "news_available": False,
            "articles_found": 0,
            "sample_headlines": [],
            "error": None
        }
        
        try:
            # 各キーワードで検索
            for keyword in keywords[:3]:  # 最初の3つのキーワードをテスト
                try:
                    headlines = ek.get_news_headlines(
                        query=keyword,
                        count=self.config.get("test_settings", {}).get("max_news_items", 5)
                    )
                    
                    if headlines is not None and len(headlines) > 0:
                        result["news_available"] = True
                        result["articles_found"] += len(headlines)
                        # サンプルヘッドラインを追加
                        for _, row in headlines.head(2).iterrows():
                            result["sample_headlines"].append({
                                "keyword": keyword,
                                "headline": row.get('text', 'N/A'),
                                "date": row.get('versionCreated', 'N/A')
                            })
                        
                        self.logger.info(f"✅ ニュース検索成功: '{keyword}' - {len(headlines)}件")
                        break  # 成功したら次のキーワードは試さない
                    
                except Exception as keyword_error:
                    self.logger.debug(f"キーワード '{keyword}' 検索失敗: {keyword_error}")
                    continue
                
                time.sleep(0.5)  # キーワード間の短い間隔
            
            if not result["news_available"]:
                result["error"] = "すべてのキーワードで検索失敗"
                self.logger.warning(f"⚠️  ニュース検索失敗: {keywords}")
                
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ ニュース検索エラー: {keywords} - {e}")
        
        time.sleep(self.config.get("test_settings", {}).get("delay_between_calls", 1.0))
        return result
    
    def explore_category_1_fundamentals(self) -> Dict[str, Any]:
        """カテゴリー1: リアルタイムの需給ファンダメンタルズ"""
        self.logger.info("=" * 60)
        self.logger.info("カテゴリー1: リアルタイムの需給ファンダメンタルズ")
        self.logger.info("=" * 60)
        
        category_results = {}
        targets = self.config["exploration_targets"]["category_1_fundamentals"]
        
        # 1.1 在庫データ
        self.logger.info("\n--- 1.1 在庫データ ---")
        inventory_results = {}
        
        inventory_rics = targets["inventory_data"]
        for name, ric in inventory_rics.items():
            if isinstance(ric, str) and ric.startswith(('0#', '.')):
                # RICコードの場合
                inventory_results[name] = self.test_ric_access(ric, f"在庫データ - {name}")
            elif name == "smm_keywords":
                # キーワード検索の場合
                inventory_results[name] = self.test_news_search(ric, f"SMM在庫情報検索")
        
        category_results["inventory_data"] = inventory_results
        
        # 1.2 生産・供給データ
        self.logger.info("\n--- 1.2 生産・供給データ ---")
        production_results = {}
        
        supply_targets = targets["production_supply"]
        # 企業名とキーワードの組み合わせでニュース検索
        combined_keywords = supply_targets["major_companies"] + supply_targets["supply_keywords"]
        production_results["supply_news"] = self.test_news_search(
            combined_keywords[:5], "生産・供給関連ニュース"
        )
        
        category_results["production_supply"] = production_results
        
        # 1.3 物流・輸送データ
        self.logger.info("\n--- 1.3 物流・輸送データ ---")
        logistics_results = {}
        
        logistics_targets = targets["logistics_transport"]
        
        # バルチック指数
        logistics_results["baltic_index"] = self.test_ric_access(
            logistics_targets["baltic_index"], "バルチック海運指数"
        )
        logistics_results["baltic_timeseries"] = self.test_timeseries_access(
            logistics_targets["baltic_index"], "バルチック指数時系列"
        )
        
        # 港湾情報（ニュース検索）
        logistics_results["port_news"] = self.test_news_search(
            logistics_targets["major_ports"], "主要港湾情報"
        )
        
        # LME倉庫待ち行列（可能であれば）
        if "lme_queues" in logistics_targets:
            logistics_results["lme_queues"] = self.test_ric_access(
                logistics_targets["lme_queues"], "LME倉庫待ち行列"
            )
        
        category_results["logistics_transport"] = logistics_results
        
        return category_results
    
    def explore_category_2_forward_looking(self) -> Dict[str, Any]:
        """カテゴリー2: フォワードルッキングなデータ"""
        self.logger.info("=" * 60)
        self.logger.info("カテゴリー2: フォワードルッキングなデータ")
        self.logger.info("=" * 60)
        
        category_results = {}
        targets = self.config["exploration_targets"]["category_2_forward_looking"]
        
        # 2.1 現物プレミアム
        self.logger.info("\n--- 2.1 現物プレミアム ---")
        premium_results = {}
        
        premium_rics = targets["physical_premiums"]
        for name, ric in premium_rics.items():
            if isinstance(ric, str) and not ric.startswith('keywords'):
                premium_results[name] = self.test_ric_access(ric, f"現物プレミアム - {name}")
                premium_results[f"{name}_timeseries"] = self.test_timeseries_access(ric, f"プレミアム時系列 - {name}")
        
        # プレミアム関連ニュース
        if "keywords" in premium_rics:
            premium_results["premium_news"] = self.test_news_search(
                premium_rics["keywords"], "現物プレミアム関連ニュース"
            )
        
        category_results["physical_premiums"] = premium_results
        
        # 2.2 アナリストレポート
        self.logger.info("\n--- 2.2 アナリストレポート ---")
        analyst_results = {}
        
        analyst_targets = targets["analyst_reports"]
        combined_search = analyst_targets["contributors"] + analyst_targets["keywords"]
        analyst_results["analyst_research"] = self.test_news_search(
            combined_search[:5], "アナリスト調査レポート"
        )
        
        category_results["analyst_reports"] = analyst_results
        
        # 2.3 川下産業データ
        self.logger.info("\n--- 2.3 川下産業データ ---")
        downstream_results = {}
        
        downstream_targets = targets["downstream_data"]
        
        # PMI指標
        for indicator_name, ric in downstream_targets.items():
            if isinstance(ric, str):
                downstream_results[indicator_name] = self.test_ric_access(ric, f"経済指標 - {indicator_name}")
            elif isinstance(ric, list):
                for i, individual_ric in enumerate(ric):
                    downstream_results[f"{indicator_name}_{i}"] = self.test_ric_access(
                        individual_ric, f"経済指標 - {indicator_name}[{i}]"
                    )
        
        category_results["downstream_data"] = downstream_results
        
        return category_results
    
    def explore_category_3_positioning(self) -> Dict[str, Any]:
        """カテゴリー3: 市場参加者のポジションとセンチメント"""
        self.logger.info("=" * 60)
        self.logger.info("カテゴリー3: 市場参加者のポジションとセンチメント")
        self.logger.info("=" * 60)
        
        category_results = {}
        targets = self.config["exploration_targets"]["category_3_positioning"]
        
        # 3.1 CFTC データ
        self.logger.info("\n--- 3.1 CFTC建玉データ ---")
        cftc_results = {}
        
        cftc_targets = targets["cftc_data"]
        for name, ric in cftc_targets.items():
            if isinstance(ric, str) and ric.startswith('0#'):
                cftc_results[name] = self.test_ric_access(ric, f"CFTC - {name}")
            elif name == "keywords":
                cftc_results["cftc_news"] = self.test_news_search(ric, "CFTC関連ニュース")
        
        category_results["cftc_data"] = cftc_results
        
        # 3.2 LME ポジション
        self.logger.info("\n--- 3.2 LMEポジション ---")
        lme_position_results = {}
        
        lme_targets = targets["lme_positions"]
        for name, ric in lme_targets.items():
            if isinstance(ric, str) and ric.startswith('0#'):
                lme_position_results[name] = self.test_ric_access(ric, f"LMEポジション - {name}")
            else:
                # ニュース検索
                lme_position_results[name] = self.test_news_search([ric], f"LMEポジション - {name}")
        
        category_results["lme_positions"] = lme_position_results
        
        # 3.3 オプションデータ
        self.logger.info("\n--- 3.3 オプションデータ ---")
        options_results = {}
        
        options_targets = targets["options_data"]
        for name, ric in options_targets.items():
            options_results[name] = self.test_ric_access(ric, f"オプション - {name}")
            # オプション関連の詳細データも試行
            options_results[f"{name}_detailed"] = self.test_ric_access(
                f"{ric}IVOL", f"オプションIV - {name}"
            )
        
        category_results["options_data"] = options_results
        
        return category_results
    
    def explore_category_4_interest_rates(self) -> Dict[str, Any]:
        """カテゴリー4: 金利と資金調達コスト"""
        self.logger.info("=" * 60)
        self.logger.info("カテゴリー4: 金利と資金調達コスト")
        self.logger.info("=" * 60)
        
        category_results = {}
        targets = self.config["exploration_targets"]["category_4_interest_rates"]
        
        # 4.1 イールドカーブ
        self.logger.info("\n--- 4.1 イールドカーブ ---")
        yield_results = {}
        
        yield_targets = targets["yield_curves"]
        for currency, rics in yield_targets.items():
            currency_results = {}
            for i, ric in enumerate(rics):
                currency_results[f"tenor_{i}"] = self.test_ric_access(ric, f"{currency} 金利")
                currency_results[f"tenor_{i}_ts"] = self.test_timeseries_access(ric, f"{currency} 金利時系列")
            yield_results[currency] = currency_results
        
        category_results["yield_curves"] = yield_results
        
        # 4.2 中央銀行政策金利
        self.logger.info("\n--- 4.2 中央銀行政策金利 ---")
        cb_results = {}
        
        cb_targets = targets["central_bank_rates"]
        for name, ric in cb_targets.items():
            cb_results[name] = self.test_ric_access(ric, f"政策金利 - {name}")
            cb_results[f"{name}_timeseries"] = self.test_timeseries_access(ric, f"政策金利時系列 - {name}")
        
        category_results["central_bank_rates"] = cb_results
        
        return category_results
    
    def run_full_exploration(self) -> Dict[str, Any]:
        """全カテゴリーの包括的探索"""
        self.logger.info("🚀 Refinitivデータ探索開始")
        self.logger.info(f"開始時刻: {datetime.now()}")
        
        exploration_results = {
            "metadata": {
                "exploration_date": datetime.now().isoformat(),
                "total_categories": 4,
                "api_key_configured": bool(self.config.get("eikon_api_key"))
            }
        }
        
        try:
            # カテゴリー1: リアルタイムの需給ファンダメンタルズ
            exploration_results["category_1_fundamentals"] = self.explore_category_1_fundamentals()
            
            # カテゴリー2: フォワードルッキングなデータ
            exploration_results["category_2_forward_looking"] = self.explore_category_2_forward_looking()
            
            # カテゴリー3: 市場参加者のポジションとセンチメント
            exploration_results["category_3_positioning"] = self.explore_category_3_positioning()
            
            # カテゴリー4: 金利と資金調達コスト
            exploration_results["category_4_interest_rates"] = self.explore_category_4_interest_rates()
            
            self.logger.info("✅ 全探索完了")
            
        except Exception as e:
            self.logger.error(f"❌ 探索中にエラー: {e}")
            exploration_results["error"] = str(e)
        
        self.results = exploration_results
        return exploration_results
    
    def generate_summary_report(self) -> str:
        """サマリーレポート生成"""
        if not self.results:
            return "探索結果がありません。run_full_exploration()を実行してください。"
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("Refinitiv Data Explorer - 探索結果サマリー")
        report_lines.append("=" * 80)
        report_lines.append(f"探索実行日時: {self.results['metadata']['exploration_date']}")
        report_lines.append("")
        
        # 各カテゴリーの結果をサマリー
        categories = [
            ("category_1_fundamentals", "カテゴリー1: リアルタイムの需給ファンダメンタルズ"),
            ("category_2_forward_looking", "カテゴリー2: フォワードルッキングなデータ"),
            ("category_3_positioning", "カテゴリー3: 市場参加者のポジションとセンチメント"),
            ("category_4_interest_rates", "カテゴリー4: 金利と資金調達コスト")
        ]
        
        total_tests = 0
        total_successful = 0
        
        for category_key, category_name in categories:
            if category_key in self.results:
                report_lines.append(f"\n{category_name}")
                report_lines.append("-" * len(category_name))
                
                category_data = self.results[category_key]
                category_tests = 0
                category_successful = 0
                
                # 各サブカテゴリーを走査
                for subcategory, subcategory_data in category_data.items():
                    if isinstance(subcategory_data, dict):
                        for test_name, test_result in subcategory_data.items():
                            if isinstance(test_result, dict):
                                category_tests += 1
                                total_tests += 1
                                
                                # 成功の判定
                                is_successful = (
                                    test_result.get("accessible", False) or
                                    test_result.get("timeseries_available", False) or
                                    test_result.get("news_available", False)
                                )
                                
                                if is_successful:
                                    category_successful += 1
                                    total_successful += 1
                                    status = "✅"
                                else:
                                    status = "❌"
                                
                                # テスト結果の詳細
                                description = test_result.get("description", test_name)
                                ric = test_result.get("ric", "")
                                error = test_result.get("error", "")
                                
                                if ric:
                                    report_lines.append(f"  {status} {description} ({ric})")
                                else:
                                    report_lines.append(f"  {status} {description}")
                                
                                if error and not is_successful:
                                    report_lines.append(f"      エラー: {error}")
                
                # カテゴリーサマリー
                success_rate = (category_successful / category_tests * 100) if category_tests > 0 else 0
                report_lines.append(f"  📊 成功率: {category_successful}/{category_tests} ({success_rate:.1f}%)")
        
        # 全体サマリー
        overall_success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
        report_lines.append(f"\n" + "=" * 80)
        report_lines.append(f"📈 全体結果: {total_successful}/{total_tests} ({overall_success_rate:.1f}%)")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)

def main():
    """メイン実行関数"""
    try:
        explorer = RefinitivDataExplorer()
        
        print("🔍 Refinitivデータ探索システム")
        print("=" * 50)
        print("既存システムに影響を与えない独立探索プロジェクト")
        print("=" * 50)
        
        # 全探索実行
        results = explorer.run_full_exploration()
        
        # サマリーレポート生成・表示
        summary = explorer.generate_summary_report()
        print("\n" + summary)
        
        # 結果をJSONファイルに保存
        output_file = f"exploration_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 詳細結果を保存: {output_file}")
        
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())