#!/usr/bin/env python3
"""
Refinitiv Data Web Claude Reporter
Web版Claude用のスプレッド予測データ取得・レポート生成システム

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

class RefinitivWebClaudeReporter:
    """Web版Claude用データレポート生成器"""
    
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
        logger = logging.getLogger('WebClaudeReporter')
        logger.setLevel(logging.INFO)
        
        # コンソール出力
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def get_inventory_data(self) -> Dict[str, Any]:
        """在庫データ取得"""
        self.logger.info("在庫データ取得開始...")
        
        inventory_data = {
            "timestamp": datetime.now().isoformat(),
            "lme_stocks": {},
            "other_exchanges": {},
            "smm_news": []
        }
        
        try:
            # LME在庫データ
            lme_data, lme_err = ek.get_data("0#LME-STOCKS", ['CF_NAME', 'CF_LAST', 'CF_DATE'])
            if lme_data is not None and not lme_data.empty:
                for _, row in lme_data.iterrows():
                    name = row.get('CF_NAME', 'Unknown')
                    value = row.get('CF_LAST', 'N/A')
                    date = row.get('CF_DATE', 'N/A')
                    inventory_data["lme_stocks"][name] = {
                        "value": value,
                        "date": str(date),
                        "unit": "tonnes"
                    }
            
            # SHFE在庫データ
            shfe_data, shfe_err = ek.get_data("0#SGH-STOCKS", ['CF_NAME', 'CF_LAST', 'CF_DATE'])
            if shfe_data is not None and not shfe_data.empty:
                inventory_data["other_exchanges"]["SHFE"] = []
                for _, row in shfe_data.iterrows():
                    inventory_data["other_exchanges"]["SHFE"].append({
                        "name": row.get('CF_NAME', 'Unknown'),
                        "value": row.get('CF_LAST', 'N/A'),
                        "date": str(row.get('CF_DATE', 'N/A'))
                    })
            
            # COMEX在庫データ
            comex_data, comex_err = ek.get_data("0#HG-STOCK", ['CF_NAME', 'CF_LAST', 'CF_DATE'])
            if comex_data is not None and not comex_data.empty:
                inventory_data["other_exchanges"]["COMEX"] = []
                for _, row in comex_data.iterrows():
                    inventory_data["other_exchanges"]["COMEX"].append({
                        "name": row.get('CF_NAME', 'Unknown'),
                        "value": row.get('CF_LAST', 'N/A'),
                        "date": str(row.get('CF_DATE', 'N/A'))
                    })
            
            # SMM関連ニュース
            try:
                smm_headlines = ek.get_news_headlines(query="SMM shadow inventory", count=5)
                if smm_headlines is not None and len(smm_headlines) > 0:
                    for _, row in smm_headlines.iterrows():
                        inventory_data["smm_news"].append({
                            "headline": row.get('text', 'N/A'),
                            "date": str(row.get('versionCreated', 'N/A')),
                            "source": row.get('sourceCode', 'N/A')
                        })
            except Exception as news_err:
                self.logger.warning(f"SMM ニュース取得エラー: {news_err}")
            
            time.sleep(1)  # API制限対策
            
        except Exception as e:
            self.logger.error(f"在庫データ取得エラー: {e}")
            inventory_data["error"] = str(e)
        
        return inventory_data
    
    def get_shipping_logistics_data(self) -> Dict[str, Any]:
        """物流・輸送データ取得"""
        self.logger.info("物流・輸送データ取得開始...")
        
        logistics_data = {
            "timestamp": datetime.now().isoformat(),
            "baltic_index": {},
            "port_news": [],
            "lme_queue_data": {}
        }
        
        try:
            # バルチック指数
            baltic_data, baltic_err = ek.get_data(".BADI", ['CF_LAST', 'CF_DATE', 'CF_NAME'])
            if baltic_data is not None and not baltic_data.empty:
                row = baltic_data.iloc[0]
                logistics_data["baltic_index"] = {
                    "value": row.get('CF_LAST', 'N/A'),
                    "date": str(row.get('CF_DATE', 'N/A')),
                    "name": row.get('CF_NAME', 'Baltic Dry Index')
                }
                
                # 時系列データも取得
                end_date = datetime.now()
                start_date = end_date - timedelta(days=30)
                baltic_ts = ek.get_timeseries(
                    ".BADI",
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    fields=['CLOSE']
                )
                if baltic_ts is not None and not baltic_ts.empty:
                    logistics_data["baltic_index"]["30day_trend"] = {
                        "start_value": float(baltic_ts['CLOSE'].iloc[0]),
                        "end_value": float(baltic_ts['CLOSE'].iloc[-1]),
                        "change_pct": ((float(baltic_ts['CLOSE'].iloc[-1]) - float(baltic_ts['CLOSE'].iloc[0])) / float(baltic_ts['CLOSE'].iloc[0])) * 100,
                        "data_points": len(baltic_ts)
                    }
            
            # 主要港湾ニュース
            port_keywords = ["Shanghai port", "Rotterdam port", "shipping delay", "port congestion"]
            for keyword in port_keywords[:2]:  # 最初の2つをテスト
                try:
                    port_headlines = ek.get_news_headlines(query=keyword, count=3)
                    if port_headlines is not None and len(port_headlines) > 0:
                        for _, row in port_headlines.iterrows():
                            logistics_data["port_news"].append({
                                "keyword": keyword,
                                "headline": row.get('text', 'N/A'),
                                "date": str(row.get('versionCreated', 'N/A')),
                                "source": row.get('sourceCode', 'N/A')
                            })
                    time.sleep(0.5)  # キーワード間の短い間隔
                except Exception as port_err:
                    self.logger.debug(f"港湾ニュース取得エラー ({keyword}): {port_err}")
            
            # LME倉庫待ち行列
            try:
                lme_queue_data, queue_err = ek.get_data("LMEQ", ['CF_NAME', 'CF_LAST'])
                if lme_queue_data is not None and not lme_queue_data.empty:
                    logistics_data["lme_queue_data"] = {
                        "queue_info": lme_queue_data.to_dict('records'),
                        "data_points": len(lme_queue_data)
                    }
            except Exception as queue_err:
                self.logger.debug(f"LME待ち行列データ取得エラー: {queue_err}")
            
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"物流データ取得エラー: {e}")
            logistics_data["error"] = str(e)
        
        return logistics_data
    
    def get_premiums_and_sentiment(self) -> Dict[str, Any]:
        """現物プレミアムとセンチメントデータ取得"""
        self.logger.info("プレミアム・センチメントデータ取得開始...")
        
        sentiment_data = {
            "timestamp": datetime.now().isoformat(),
            "physical_premiums": {},
            "cftc_positions": {},
            "options_data": {},
            "analyst_sentiment": []
        }
        
        try:
            # 現物プレミアム
            premium_rics = ["AL-PREM-JP", "CU-PREM-SH"]
            for ric in premium_rics:
                try:
                    prem_data, prem_err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    if prem_data is not None and not prem_data.empty:
                        row = prem_data.iloc[0]
                        sentiment_data["physical_premiums"][ric] = {
                            "value": row.get('CF_LAST', 'N/A'),
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "name": row.get('CF_NAME', ric)
                        }
                except Exception as prem_err:
                    self.logger.debug(f"プレミアムデータ取得エラー ({ric}): {prem_err}")
            
            # CFTC建玉データ
            cftc_rics = ["0#CFTC-COPPER:", "0#CFTC-ALUM:"]
            for ric in cftc_rics:
                try:
                    cftc_data, cftc_err = ek.get_data(ric, ['CF_NAME', 'CF_LAST', 'CF_DATE'])
                    if cftc_data is not None and not cftc_data.empty:
                        sentiment_data["cftc_positions"][ric] = {
                            "positions": cftc_data.to_dict('records'),
                            "data_points": len(cftc_data)
                        }
                except Exception as cftc_err:
                    self.logger.debug(f"CFTCデータ取得エラー ({ric}): {cftc_err}")
            
            # オプションIVデータ
            option_rics = ["CMCU=IVOL", "CMAL=IVOL"]
            for ric in option_rics:
                try:
                    iv_data, iv_err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    if iv_data is not None and not iv_data.empty:
                        row = iv_data.iloc[0]
                        sentiment_data["options_data"][ric] = {
                            "implied_volatility": row.get('CF_LAST', 'N/A'),
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "name": row.get('CF_NAME', ric)
                        }
                except Exception as iv_err:
                    self.logger.debug(f"オプションIVデータ取得エラー ({ric}): {iv_err}")
            
            # アナリスト・レポート関連ニュース
            analyst_keywords = ["Macquarie copper", "Goldman Sachs metals", "JPMorgan commodity"]
            for keyword in analyst_keywords:
                try:
                    analyst_headlines = ek.get_news_headlines(query=keyword, count=2)
                    if analyst_headlines is not None and len(analyst_headlines) > 0:
                        for _, row in analyst_headlines.iterrows():
                            sentiment_data["analyst_sentiment"].append({
                                "keyword": keyword,
                                "headline": row.get('text', 'N/A'),
                                "date": str(row.get('versionCreated', 'N/A')),
                                "source": row.get('sourceCode', 'N/A')
                            })
                    time.sleep(0.5)
                except Exception as analyst_err:
                    self.logger.debug(f"アナリストニュース取得エラー ({keyword}): {analyst_err}")
            
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"センチメントデータ取得エラー: {e}")
            sentiment_data["error"] = str(e)
        
        return sentiment_data
    
    def get_macro_economic_data(self) -> Dict[str, Any]:
        """マクロ経済データ取得"""
        self.logger.info("マクロ経済データ取得開始...")
        
        macro_data = {
            "timestamp": datetime.now().isoformat(),
            "pmi_indicators": {},
            "auto_sales": {},
            "fixed_investment": {},
            "interest_rates": {}
        }
        
        try:
            # PMI指標
            pmi_rics = {
                "china_pmi": "CN.PMIMFG.IDX",
                "us_pmi": "US.PMIMFG.IDX", 
                "eu_pmi": "EU.PMIMFG.IDX"
            }
            
            for name, ric in pmi_rics.items():
                try:
                    pmi_data, pmi_err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    if pmi_data is not None and not pmi_data.empty:
                        row = pmi_data.iloc[0]
                        macro_data["pmi_indicators"][name] = {
                            "value": row.get('CF_LAST', 'N/A'),
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "name": row.get('CF_NAME', name)
                        }
                except Exception as pmi_err:
                    self.logger.debug(f"PMIデータ取得エラー ({name}): {pmi_err}")
            
            # 自動車販売
            auto_rics = {
                "china_auto": "CN.AUTOSALES",
                "us_auto": "US.AUTOSALES"
            }
            
            for name, ric in auto_rics.items():
                try:
                    auto_data, auto_err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    if auto_data is not None and not auto_data.empty:
                        row = auto_data.iloc[0]
                        macro_data["auto_sales"][name] = {
                            "value": row.get('CF_LAST', 'N/A'),
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "name": row.get('CF_NAME', name)
                        }
                except Exception as auto_err:
                    self.logger.debug(f"自動車販売データ取得エラー ({name}): {auto_err}")
            
            # 中国固定資産投資
            try:
                fixed_data, fixed_err = ek.get_data("CN.FIXEDINV.YOY", ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                if fixed_data is not None and not fixed_data.empty:
                    row = fixed_data.iloc[0]
                    macro_data["fixed_investment"] = {
                        "value": row.get('CF_LAST', 'N/A'),
                        "date": str(row.get('CF_DATE', 'N/A')),
                        "name": row.get('CF_NAME', 'China Fixed Investment YoY')
                    }
            except Exception as fixed_err:
                self.logger.debug(f"固定投資データ取得エラー: {fixed_err}")
            
            # 主要政策金利
            rate_rics = {
                "fed_funds": "USDFF=",
                "ecb_rate": "EUREPO=",
                "pboc_rate": "CNREPO="
            }
            
            for name, ric in rate_rics.items():
                try:
                    rate_data, rate_err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    if rate_data is not None and not rate_data.empty:
                        row = rate_data.iloc[0]
                        macro_data["interest_rates"][name] = {
                            "value": row.get('CF_LAST', 'N/A'),
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "name": row.get('CF_NAME', name)
                        }
                except Exception as rate_err:
                    self.logger.debug(f"金利データ取得エラー ({name}): {rate_err}")
            
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"マクロ経済データ取得エラー: {e}")
            macro_data["error"] = str(e)
        
        return macro_data
    
    def generate_web_claude_report(self) -> str:
        """Web版Claude用テキストレポート生成"""
        self.logger.info("Web版Claude用レポート生成開始...")
        
        # 各カテゴリーのデータ取得
        inventory_data = self.get_inventory_data()
        logistics_data = self.get_shipping_logistics_data()
        sentiment_data = self.get_premiums_and_sentiment()
        macro_data = self.get_macro_economic_data()
        
        # レポート生成
        report_lines = []
        
        # ヘッダー
        report_lines.append("=" * 80)
        report_lines.append("【Web版Claude用】スプレッド予測精度向上データレポート")
        report_lines.append("=" * 80)
        report_lines.append(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        report_lines.append(f"データソース: Refinitiv EIKON API")
        report_lines.append("")
        
        # プロンプト部分
        report_lines.append("【Claude分析用プロンプト】")
        report_lines.append("以下のRefinitivから取得したリアルタイム金属市場データを基に、")
        report_lines.append("LME金属先物スプレッド（コンタンゴ/バックワーデーション）の予測分析を行ってください。")
        report_lines.append("")
        report_lines.append("【分析要件】")
        report_lines.append("- 各データポイントが示すスプレッド方向への影響を評価")
        report_lines.append("- 在庫状況、物流コスト、センチメント、マクロ要因の総合分析")
        report_lines.append("- 短期（1-2週間）、中期（1-3ヶ月）スプレッド予測")
        report_lines.append("- リスク要因とシナリオ分析")
        report_lines.append("- 具体的なトレーディング示唆")
        report_lines.append("")
        
        # カテゴリー1: 在庫・需給データ
        report_lines.append("=" * 60)
        report_lines.append("【カテゴリー1】リアルタイム在庫・需給データ")
        report_lines.append("=" * 60)
        
        report_lines.append("\n--- LME公式在庫 ---")
        if "lme_stocks" in inventory_data:
            for metal, data in inventory_data["lme_stocks"].items():
                if isinstance(data, dict) and "value" in data:
                    report_lines.append(f"  {metal}: {data['value']} {data.get('unit', '')} (更新: {data.get('date', 'N/A')})")
        
        report_lines.append("\n--- 他取引所在庫 ---")
        if "other_exchanges" in inventory_data:
            for exchange, stocks in inventory_data["other_exchanges"].items():
                report_lines.append(f"  【{exchange}】")
                if isinstance(stocks, list):
                    for stock in stocks[:3]:  # 最初の3つを表示
                        report_lines.append(f"    {stock.get('name', 'N/A')}: {stock.get('value', 'N/A')} (日付: {stock.get('date', 'N/A')})")
        
        report_lines.append("\n--- SMM非公表在庫情報 ---")
        if "smm_news" in inventory_data and inventory_data["smm_news"]:
            for i, news in enumerate(inventory_data["smm_news"][:3]):
                report_lines.append(f"  [{i+1}] {news.get('headline', 'N/A')}")
                report_lines.append(f"      日時: {news.get('date', 'N/A')} | ソース: {news.get('source', 'N/A')}")
        
        # カテゴリー2: 物流・輸送データ
        report_lines.append("\n" + "=" * 60)
        report_lines.append("【カテゴリー2】物流・輸送コストデータ")
        report_lines.append("=" * 60)
        
        report_lines.append("\n--- バルチック海運指数 ---")
        if "baltic_index" in logistics_data:
            baltic = logistics_data["baltic_index"]
            report_lines.append(f"  現在値: {baltic.get('value', 'N/A')} (更新: {baltic.get('date', 'N/A')})")
            if "30day_trend" in baltic:
                trend = baltic["30day_trend"]
                report_lines.append(f"  30日トレンド: {trend.get('start_value', 'N/A')} → {trend.get('end_value', 'N/A')}")
                report_lines.append(f"  変動率: {trend.get('change_pct', 'N/A'):.2f}% ({trend.get('data_points', 0)}ポイント)")
        
        report_lines.append("\n--- 主要港湾・物流ニュース ---")
        if "port_news" in logistics_data and logistics_data["port_news"]:
            for i, news in enumerate(logistics_data["port_news"][:4]):
                report_lines.append(f"  [{i+1}] ({news.get('keyword', 'N/A')}) {news.get('headline', 'N/A')}")
                report_lines.append(f"      日時: {news.get('date', 'N/A')}")
        
        # カテゴリー3: センチメント・ポジションデータ
        report_lines.append("\n" + "=" * 60)
        report_lines.append("【カテゴリー3】市場センチメント・ポジションデータ")
        report_lines.append("=" * 60)
        
        report_lines.append("\n--- 現物プレミアム ---")
        if "physical_premiums" in sentiment_data:
            for ric, data in sentiment_data["physical_premiums"].items():
                if isinstance(data, dict):
                    report_lines.append(f"  {data.get('name', ric)}: {data.get('value', 'N/A')} (更新: {data.get('date', 'N/A')})")
        
        report_lines.append("\n--- CFTC建玉明細 ---")
        if "cftc_positions" in sentiment_data:
            for ric, data in sentiment_data["cftc_positions"].items():
                if isinstance(data, dict) and "positions" in data:
                    report_lines.append(f"  【{ric}】")
                    for pos in data["positions"][:3]:
                        report_lines.append(f"    {pos.get('CF_NAME', 'N/A')}: {pos.get('CF_LAST', 'N/A')} (日付: {pos.get('CF_DATE', 'N/A')})")
        
        report_lines.append("\n--- オプション市場データ ---")
        if "options_data" in sentiment_data:
            for ric, data in sentiment_data["options_data"].items():
                if isinstance(data, dict):
                    report_lines.append(f"  {data.get('name', ric)} IV: {data.get('implied_volatility', 'N/A')}% (更新: {data.get('date', 'N/A')})")
        
        report_lines.append("\n--- アナリスト・センチメント ---")
        if "analyst_sentiment" in sentiment_data and sentiment_data["analyst_sentiment"]:
            for i, news in enumerate(sentiment_data["analyst_sentiment"][:4]):
                report_lines.append(f"  [{i+1}] ({news.get('keyword', 'N/A')}) {news.get('headline', 'N/A')}")
                report_lines.append(f"      日時: {news.get('date', 'N/A')}")
        
        # カテゴリー4: マクロ経済データ
        report_lines.append("\n" + "=" * 60)
        report_lines.append("【カテゴリー4】マクロ経済・金利データ")
        report_lines.append("=" * 60)
        
        report_lines.append("\n--- 製造業PMI指標 ---")
        if "pmi_indicators" in macro_data:
            for name, data in macro_data["pmi_indicators"].items():
                if isinstance(data, dict):
                    report_lines.append(f"  {data.get('name', name)}: {data.get('value', 'N/A')} (更新: {data.get('date', 'N/A')})")
        
        report_lines.append("\n--- 自動車販売統計 ---")
        if "auto_sales" in macro_data:
            for name, data in macro_data["auto_sales"].items():
                if isinstance(data, dict):
                    report_lines.append(f"  {data.get('name', name)}: {data.get('value', 'N/A')} (更新: {data.get('date', 'N/A')})")
        
        report_lines.append("\n--- 中国固定資産投資 ---")
        if "fixed_investment" in macro_data and isinstance(macro_data["fixed_investment"], dict):
            fixed = macro_data["fixed_investment"]
            report_lines.append(f"  {fixed.get('name', 'Fixed Investment')}: {fixed.get('value', 'N/A')}% YoY (更新: {fixed.get('date', 'N/A')})")
        
        report_lines.append("\n--- 主要国政策金利 ---")
        if "interest_rates" in macro_data:
            for name, data in macro_data["interest_rates"].items():
                if isinstance(data, dict):
                    report_lines.append(f"  {data.get('name', name)}: {data.get('value', 'N/A')}% (更新: {data.get('date', 'N/A')})")
        
        # フッター
        report_lines.append("\n" + "=" * 80)
        report_lines.append("【分析指示】")
        report_lines.append("上記データを統合して以下の観点から分析してください：")
        report_lines.append("")
        report_lines.append("1. 在庫状況分析:")
        report_lines.append("   - LME公式在庫 vs 非公表在庫の乖離")
        report_lines.append("   - 地域別在庫分布とインプリケーション")
        report_lines.append("")
        report_lines.append("2. 物流コスト影響:")
        report_lines.append("   - バルチック指数トレンドがCarry Costに与える影響")
        report_lines.append("   - 港湾状況による現物タイト感")
        report_lines.append("")
        report_lines.append("3. 市場センチメント:")
        report_lines.append("   - 現物プレミアム変動の先行指標性")
        report_lines.append("   - CFTC投機筋ポジションの偏り")
        report_lines.append("   - オプションIVが示すリスク認識")
        report_lines.append("")
        report_lines.append("4. マクロファンダメンタルズ:")
        report_lines.append("   - PMI、自動車販売等の需要先行指標")
        report_lines.append("   - 金利環境がCost of Carryに与える影響")
        report_lines.append("")
        report_lines.append("5. スプレッド予測:")
        report_lines.append("   - コンタンゴ/バックワーデーション方向")
        report_lines.append("   - 期間構造の変化予測")
        report_lines.append("   - トレーディング戦略の提案")
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report(self, report_content: str, filename: str = None) -> str:
        """レポートをファイルに保存"""
        if filename is None:
            filename = f"Refinitiv_Spread_Analysis_Data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"レポート保存完了: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"レポート保存エラー: {e}")
            raise

def main():
    """メイン実行関数"""
    try:
        reporter = RefinitivWebClaudeReporter()
        
        print("🌐 Web版Claude用 Refinitivデータレポート生成")
        print("=" * 60)
        print("スプレッド予測精度向上のための包括的データ取得中...")
        print("=" * 60)
        
        # レポート生成
        report_content = reporter.generate_web_claude_report()
        
        # ファイル保存
        saved_filename = reporter.save_report(report_content)
        
        print(f"\n✅ レポート生成完了!")
        print(f"📄 保存ファイル: {saved_filename}")
        print(f"📊 ファイルサイズ: {len(report_content.encode('utf-8')):,} bytes")
        print("\n🔗 このファイルをWeb版Claudeにアップロードして分析を依頼してください。")
        
        return 0
        
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())