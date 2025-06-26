#!/usr/bin/env python3
"""
Enhanced Refinitiv Data Web Claude Reporter
Web版Claude用の改良版スプレッド予測データ取得・レポート生成システム

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

class EnhancedRefinitivWebClaudeReporter:
    """改良版Web版Claude用データレポート生成器"""
    
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
        logger = logging.getLogger('EnhancedWebClaudeReporter')
        logger.setLevel(logging.INFO)
        
        # コンソール出力
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def get_enhanced_lme_inventory(self) -> Dict[str, Any]:
        """改良版LME在庫データ取得（オンワラント・キャンセルワラント分解）"""
        self.logger.info("改良版LME在庫データ取得開始...")
        
        inventory_data = {
            "timestamp": datetime.now().isoformat(),
            "lme_detailed_stocks": {},
            "lme_warrant_status": {},
            "other_exchanges": {},
            "errors": []
        }
        
        try:
            # LME在庫の詳細RIC定義
            lme_detailed_rics = {
                "copper": {
                    "total": "CMCU-STX-LME",
                    "on_warrant": "CMCU-SOW-LME", 
                    "cancelled": "CMCU-SCW-LME",
                    "live_warrant": "CMCU-SLW-LME"
                },
                "aluminum": {
                    "total": "CMAL-STX-LME",
                    "on_warrant": "CMAL-SOW-LME",
                    "cancelled": "CMAL-SCW-LME", 
                    "live_warrant": "CMAL-SLW-LME"
                },
                "zinc": {
                    "total": "CMZN-STX-LME",
                    "on_warrant": "CMZN-SOW-LME",
                    "cancelled": "CMZN-SCW-LME",
                    "live_warrant": "CMZN-SLW-LME"
                },
                "lead": {
                    "total": "CMPB-STX-LME", 
                    "on_warrant": "CMPB-SOW-LME",
                    "cancelled": "CMPB-SCW-LME",
                    "live_warrant": "CMPB-SLW-LME"
                },
                "nickel": {
                    "total": "CMNI-STX-LME",
                    "on_warrant": "CMNI-SOW-LME", 
                    "cancelled": "CMNI-SCW-LME",
                    "live_warrant": "CMNI-SLW-LME"
                },
                "tin": {
                    "total": "CMSN-STX-LME",
                    "on_warrant": "CMSN-SOW-LME",
                    "cancelled": "CMSN-SCW-LME", 
                    "live_warrant": "CMSN-SLW-LME"
                }
            }
            
            # 各金属の詳細在庫データ取得
            for metal, rics in lme_detailed_rics.items():
                self.logger.info(f"{metal}在庫データ取得中...")
                inventory_data["lme_detailed_stocks"][metal] = {}
                
                for stock_type, ric in rics.items():
                    try:
                        # get_dataを使って詳細データ取得
                        data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                        
                        if data is not None and not data.empty and len(data) > 0:
                            row = data.iloc[0]
                            value = row.get('CF_LAST')
                            date = row.get('CF_DATE')
                            name = row.get('CF_NAME', ric)
                            
                            # NaNやNoneのチェック
                            if pd.notna(value) and value is not None:
                                inventory_data["lme_detailed_stocks"][metal][stock_type] = {
                                    "value": float(value),
                                    "date": str(date) if pd.notna(date) else "N/A",
                                    "ric": ric,
                                    "name": str(name) if pd.notna(name) else ric
                                }
                                self.logger.info(f"✅ {metal} {stock_type}: {value}")
                            else:
                                self.logger.warning(f"⚠️  {metal} {stock_type} データが空: {ric}")
                        else:
                            self.logger.warning(f"⚠️  {metal} {stock_type} アクセス失敗: {ric}")
                            if err:
                                inventory_data["errors"].append(f"{ric}: {err}")
                        
                        time.sleep(0.3)  # API制限対策
                        
                    except Exception as e:
                        error_msg = f"{metal} {stock_type} ({ric}): {str(e)}"
                        inventory_data["errors"].append(error_msg)
                        self.logger.error(f"❌ {error_msg}")
                
                time.sleep(0.5)  # 金属間の間隔
            
            # 代替LME在庫データ取得（0#チェーンから個別に）
            self.logger.info("代替LME在庫チェーン取得...")
            try:
                lme_chain_data, chain_err = ek.get_data("0#LME-STOCKS", ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                if lme_chain_data is not None and not lme_chain_data.empty:
                    inventory_data["lme_warrant_status"]["chain_data"] = []
                    for _, row in lme_chain_data.iterrows():
                        name = row.get('CF_NAME')
                        value = row.get('CF_LAST') 
                        date = row.get('CF_DATE')
                        
                        if pd.notna(value) and pd.notna(name):
                            inventory_data["lme_warrant_status"]["chain_data"].append({
                                "name": str(name),
                                "value": float(value),
                                "date": str(date) if pd.notna(date) else "N/A"
                            })
                    
                    self.logger.info(f"✅ LMEチェーンデータ: {len(inventory_data['lme_warrant_status']['chain_data'])}項目")
            except Exception as e:
                inventory_data["errors"].append(f"LME chain data: {str(e)}")
            
            # SHFE在庫データ（個別RIC）
            shfe_rics = {
                "copper": "CU-STX-SGH",
                "aluminum": "AL-STX-SGH", 
                "zinc": "ZN-STX-SGH",
                "lead": "PB-STX-SGH",
                "nickel": "NI-STX-SGH",
                "tin": "SN-STX-SGH"
            }
            
            inventory_data["other_exchanges"]["SHFE"] = {}
            for metal, ric in shfe_rics.items():
                try:
                    data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    if data is not None and not data.empty:
                        row = data.iloc[0]
                        value = row.get('CF_LAST')
                        if pd.notna(value):
                            inventory_data["other_exchanges"]["SHFE"][metal] = {
                                "value": float(value),
                                "date": str(row.get('CF_DATE', 'N/A')),
                                "ric": ric
                            }
                            self.logger.info(f"✅ SHFE {metal}: {value}")
                    time.sleep(0.2)
                except Exception as e:
                    inventory_data["errors"].append(f"SHFE {metal} ({ric}): {str(e)}")
            
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"在庫データ取得エラー: {e}")
            inventory_data["errors"].append(f"General inventory error: {str(e)}")
        
        return inventory_data
    
    def get_enhanced_news_data(self) -> Dict[str, Any]:
        """改良版ニュースデータ取得（本文付き）"""
        self.logger.info("改良版ニュースデータ取得開始...")
        
        news_data = {
            "timestamp": datetime.now().isoformat(),
            "market_moving_news": [],
            "analyst_reports": [],
            "supply_disruption_news": [],
            "errors": []
        }
        
        try:
            # 市場インパクトニュース
            market_keywords = [
                "LME copper inventory",
                "China PMI manufacturing",
                "Baltic dry index",
                "Goldman Sachs commodity"
            ]
            
            for keyword in market_keywords:
                try:
                    self.logger.info(f"ニュース検索: {keyword}")
                    headlines = ek.get_news_headlines(query=keyword, count=3)
                    
                    if headlines is not None and len(headlines) > 0:
                        for _, row in headlines.iterrows():
                            story_id = row.get('storyId')
                            headline = row.get('text', 'N/A')
                            date = row.get('versionCreated', 'N/A')
                            source = row.get('sourceCode', 'N/A')
                            
                            # ニュース本文取得を試行
                            news_body = "本文取得失敗"
                            if story_id:
                                try:
                                    news_story = ek.get_news_story(story_id)
                                    if news_story and len(news_story) > 100:
                                        # 最初の500文字を取得
                                        news_body = news_story[:500] + "..." if len(news_story) > 500 else news_story
                                    time.sleep(0.2)  # 本文取得間隔
                                except Exception as story_err:
                                    news_body = f"本文取得エラー: {str(story_err)}"
                            
                            news_data["market_moving_news"].append({
                                "keyword": keyword,
                                "headline": headline,
                                "body": news_body,
                                "date": str(date),
                                "source": source,
                                "story_id": story_id
                            })
                    
                    time.sleep(0.5)  # キーワード間隔
                    
                except Exception as e:
                    news_data["errors"].append(f"News search ({keyword}): {str(e)}")
            
            # 供給途絶ニュース
            supply_keywords = ["copper mine strike", "Codelco production", "shipping delay metal"]
            
            for keyword in supply_keywords[:2]:  # 制限して実行
                try:
                    headlines = ek.get_news_headlines(query=keyword, count=2)
                    
                    if headlines is not None and len(headlines) > 0:
                        for _, row in headlines.iterrows():
                            news_data["supply_disruption_news"].append({
                                "keyword": keyword,
                                "headline": row.get('text', 'N/A'),
                                "date": str(row.get('versionCreated', 'N/A')),
                                "source": row.get('sourceCode', 'N/A')
                            })
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    news_data["errors"].append(f"Supply news ({keyword}): {str(e)}")
            
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"ニュースデータ取得エラー: {e}")
            news_data["errors"].append(f"General news error: {str(e)}")
        
        return news_data
    
    def get_enhanced_macro_data(self) -> Dict[str, Any]:
        """改良版マクロ経済データ取得"""
        self.logger.info("改良版マクロ経済データ取得開始...")
        
        macro_data = {
            "timestamp": datetime.now().isoformat(),
            "economic_indicators": {},
            "commodity_indices": {},
            "currency_rates": {},
            "errors": []
        }
        
        try:
            # 確実に取得できるマクロ指標RIC
            reliable_rics = {
                "us_dollar_index": ".DXY",
                "crude_oil_wti": "CLc1",
                "copper_lme_3m": "CMCU3",
                "aluminum_lme_3m": "CMAL3",
                "usd_jpy": "JPY=",
                "usd_cny": "CNY=",
                "us_10y_yield": "US10YT=RR"
            }
            
            for name, ric in reliable_rics.items():
                try:
                    data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME', 'PCTCHNG'])
                    
                    if data is not None and not data.empty:
                        row = data.iloc[0]
                        value = row.get('CF_LAST')
                        change = row.get('PCTCHNG')
                        
                        if pd.notna(value):
                            macro_data["economic_indicators"][name] = {
                                "value": float(value),
                                "daily_change_pct": float(change) if pd.notna(change) else None,
                                "date": str(row.get('CF_DATE', 'N/A')),
                                "name": str(row.get('CF_NAME', name)),
                                "ric": ric
                            }
                            self.logger.info(f"✅ {name}: {value}")
                        
                        # 時系列トレンドも取得
                        try:
                            end_date = datetime.now()
                            start_date = end_date - timedelta(days=7)
                            ts_data = ek.get_timeseries(
                                ric,
                                start_date=start_date.strftime('%Y-%m-%d'),
                                end_date=end_date.strftime('%Y-%m-%d'),
                                fields=['CLOSE']
                            )
                            if ts_data is not None and not ts_data.empty and len(ts_data) > 1:
                                week_change = ((ts_data['CLOSE'].iloc[-1] - ts_data['CLOSE'].iloc[0]) / ts_data['CLOSE'].iloc[0]) * 100
                                macro_data["economic_indicators"][name]["weekly_change_pct"] = round(week_change, 2)
                        except:
                            pass  # 時系列データが取得できない場合はスキップ
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    error_msg = f"{name} ({ric}): {str(e)}"
                    macro_data["errors"].append(error_msg)
                    self.logger.warning(f"⚠️  {error_msg}")
            
            # バルチック指数の詳細取得
            try:
                baltic_data, err = ek.get_data(".BADI", ['CF_LAST', 'CF_DATE', 'CF_NAME', 'PCTCHNG'])
                if baltic_data is not None and not baltic_data.empty:
                    row = baltic_data.iloc[0]
                    value = row.get('CF_LAST')
                    if pd.notna(value):
                        macro_data["commodity_indices"]["baltic_dry_index"] = {
                            "value": float(value),
                            "daily_change_pct": float(row.get('PCTCHNG')) if pd.notna(row.get('PCTCHNG')) else None,
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "significance": "物流コスト指標：上昇はコンタンゴ要因"
                        }
                        
                        # 30日トレンド
                        try:
                            end_date = datetime.now()
                            start_date = end_date - timedelta(days=30)
                            baltic_ts = ek.get_timeseries(
                                ".BADI", 
                                start_date=start_date.strftime('%Y-%m-%d'),
                                end_date=end_date.strftime('%Y-%m-%d'),
                                fields=['CLOSE']
                            )
                            if baltic_ts is not None and not baltic_ts.empty:
                                month_change = ((float(value) - baltic_ts['CLOSE'].iloc[0]) / baltic_ts['CLOSE'].iloc[0]) * 100
                                macro_data["commodity_indices"]["baltic_dry_index"]["monthly_change_pct"] = round(month_change, 2)
                                self.logger.info(f"✅ バルチック指数: {value} (月次変動: {month_change:.2f}%)")
                        except:
                            pass
            except Exception as e:
                macro_data["errors"].append(f"Baltic index: {str(e)}")
            
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"マクロデータ取得エラー: {e}")
            macro_data["errors"].append(f"General macro error: {str(e)}")
        
        return macro_data
    
    def generate_enhanced_web_claude_report(self) -> str:
        """改良版Web版Claude用テキストレポート生成"""
        self.logger.info("改良版Web版Claude用レポート生成開始...")
        
        # 各カテゴリーのデータ取得
        inventory_data = self.get_enhanced_lme_inventory()
        news_data = self.get_enhanced_news_data()
        macro_data = self.get_enhanced_macro_data()
        
        # レポート生成
        report_lines = []
        
        # ヘッダー
        report_lines.append("=" * 80)
        report_lines.append("【Web版Claude用】改良版スプレッド予測精度向上データレポート")
        report_lines.append("=" * 80)
        report_lines.append(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        report_lines.append(f"データソース: Refinitiv EIKON API（改良版）")
        report_lines.append("")
        
        # プロンプト部分
        report_lines.append("【Claude分析用プロンプト】")
        report_lines.append("以下のRefinitivから取得したリアルタイム金属市場データを基に、")
        report_lines.append("LME金属先物スプレッド（コンタンゴ/バックワーデーション）の予測分析を行ってください。")
        report_lines.append("")
        report_lines.append("【重要な分析要件】")
        report_lines.append("- LME在庫のオンワラント vs キャンセルワラントの構造分析")
        report_lines.append("- 物流コスト（バルチック指数）変動がCarry Costに与える影響")
        report_lines.append("- 最新ニュース・アナリスト見解のセンチメント分析")
        report_lines.append("- マクロ経済指標とコモディティ価格の相関分析")
        report_lines.append("- 短期（1-2週間）・中期（1-3ヶ月）スプレッド方向予測")
        report_lines.append("- 具体的なトレーディング戦略とリスクシナリオ")
        report_lines.append("")
        
        # カテゴリー1: 詳細在庫データ
        report_lines.append("=" * 60)
        report_lines.append("【カテゴリー1】LME在庫詳細データ（ワラント分解）")
        report_lines.append("=" * 60)
        
        if "lme_detailed_stocks" in inventory_data:
            for metal, stock_data in inventory_data["lme_detailed_stocks"].items():
                if stock_data:  # データが存在する場合のみ表示
                    report_lines.append(f"\n--- {metal.upper()}在庫構造 ---")
                    
                    total_stock = stock_data.get("total", {}).get("value", "N/A")
                    on_warrant = stock_data.get("on_warrant", {}).get("value", "N/A")
                    cancelled = stock_data.get("cancelled", {}).get("value", "N/A")
                    
                    report_lines.append(f"  総在庫量: {total_stock} トン")
                    report_lines.append(f"  オンワラント: {on_warrant} トン")
                    report_lines.append(f"  キャンセルワラント: {cancelled} トン")
                    
                    # 比率計算
                    if isinstance(total_stock, (int, float)) and isinstance(cancelled, (int, float)) and total_stock > 0:
                        cancel_ratio = (cancelled / total_stock) * 100
                        report_lines.append(f"  キャンセル率: {cancel_ratio:.1f}% (バックワーデーション要因)")
                    
                    date = stock_data.get("total", {}).get("date", "N/A")
                    report_lines.append(f"  更新日: {date}")
        
        # チェーンデータからの補完
        if "lme_warrant_status" in inventory_data and "chain_data" in inventory_data["lme_warrant_status"]:
            report_lines.append(f"\n--- LME在庫サマリー（チェーンデータ） ---")
            for item in inventory_data["lme_warrant_status"]["chain_data"]:
                name = item.get("name", "N/A")
                value = item.get("value", "N/A")
                date = item.get("date", "N/A")
                report_lines.append(f"  {name}: {value} トン (更新: {date})")
        
        # SHFE在庫比較
        if "other_exchanges" in inventory_data and "SHFE" in inventory_data["other_exchanges"]:
            report_lines.append(f"\n--- SHFE在庫（地域比較用） ---")
            for metal, data in inventory_data["other_exchanges"]["SHFE"].items():
                value = data.get("value", "N/A")
                date = data.get("date", "N/A")
                report_lines.append(f"  {metal.capitalize()}: {value} トン (更新: {date})")
        
        # カテゴリー2: 市場インパクトニュース
        report_lines.append("\n" + "=" * 60)
        report_lines.append("【カテゴリー2】市場インパクトニュース（本文付き）")
        report_lines.append("=" * 60)
        
        if "market_moving_news" in news_data and news_data["market_moving_news"]:
            for i, news in enumerate(news_data["market_moving_news"][:6]):
                report_lines.append(f"\n--- ニュース {i+1} ({news.get('keyword', 'N/A')}) ---")
                report_lines.append(f"見出し: {news.get('headline', 'N/A')}")
                report_lines.append(f"本文: {news.get('body', 'N/A')}")
                report_lines.append(f"日時: {news.get('date', 'N/A')} | ソース: {news.get('source', 'N/A')}")
        
        if "supply_disruption_news" in news_data and news_data["supply_disruption_news"]:
            report_lines.append(f"\n--- 供給途絶関連ニュース ---")
            for news in news_data["supply_disruption_news"]:
                report_lines.append(f"  • {news.get('headline', 'N/A')}")
                report_lines.append(f"    日時: {news.get('date', 'N/A')} | キーワード: {news.get('keyword', 'N/A')}")
        
        # カテゴリー3: マクロ経済・コモディティ指標
        report_lines.append("\n" + "=" * 60)
        report_lines.append("【カテゴリー3】マクロ経済・コモディティ指標")
        report_lines.append("=" * 60)
        
        if "economic_indicators" in macro_data:
            report_lines.append(f"\n--- 主要経済指標 ---")
            for name, data in macro_data["economic_indicators"].items():
                value = data.get("value", "N/A")
                daily_chg = data.get("daily_change_pct", "N/A")
                weekly_chg = data.get("weekly_change_pct", "N/A")
                date = data.get("date", "N/A")
                
                report_lines.append(f"  {data.get('name', name)}: {value}")
                if daily_chg != "N/A":
                    report_lines.append(f"    日次変動: {daily_chg:+.2f}%")
                if weekly_chg != "N/A":
                    report_lines.append(f"    週次変動: {weekly_chg:+.2f}%")
                report_lines.append(f"    更新: {date}")
                report_lines.append("")
        
        if "commodity_indices" in macro_data:
            report_lines.append(f"--- 物流・運賃指標 ---")
            for name, data in macro_data["commodity_indices"].items():
                value = data.get("value", "N/A")
                daily_chg = data.get("daily_change_pct", "N/A")
                monthly_chg = data.get("monthly_change_pct", "N/A")
                significance = data.get("significance", "")
                
                report_lines.append(f"  {name}: {value}")
                if daily_chg != "N/A":
                    report_lines.append(f"    日次変動: {daily_chg:+.2f}%")
                if monthly_chg != "N/A":
                    report_lines.append(f"    月次変動: {monthly_chg:+.2f}%")
                if significance:
                    report_lines.append(f"    意義: {significance}")
                report_lines.append("")
        
        # エラーサマリー
        all_errors = []
        all_errors.extend(inventory_data.get("errors", []))
        all_errors.extend(news_data.get("errors", []))
        all_errors.extend(macro_data.get("errors", []))
        
        if all_errors:
            report_lines.append(f"\n--- データ取得エラー・制限事項 ---")
            for error in all_errors[:10]:  # 最初の10個のエラーを表示
                report_lines.append(f"  • {error}")
        
        # フッター・分析指示
        report_lines.append("\n" + "=" * 80)
        report_lines.append("【詳細分析指示】")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("以下の観点から総合的なスプレッド分析を実施してください：")
        report_lines.append("")
        report_lines.append("1. 在庫構造分析:")
        report_lines.append("   - キャンセルワラント比率の高い金属 → バックワーデーション圧力")
        report_lines.append("   - LME vs SHFE在庫比較 → 地域需給格差")
        report_lines.append("   - オンワラント減少トレンド → 現物タイト化")
        report_lines.append("")
        report_lines.append("2. 物流コスト要因:")
        report_lines.append("   - バルチック指数上昇 → 輸送費増加 → コンタンゴ拡大要因")
        report_lines.append("   - 週次・月次トレンド継続性評価")
        report_lines.append("")
        report_lines.append("3. マーケットセンチメント:")
        report_lines.append("   - ニュース本文から読み取れる市場心理")
        report_lines.append("   - アナリスト見解の方向性（強気/弱気）")
        report_lines.append("   - 供給途絶リスクの定量的影響")
        report_lines.append("")
        report_lines.append("4. マクロ環境:")
        report_lines.append("   - ドル指数・金利変動がCarry Costに与える影響")
        report_lines.append("   - 原油価格とメタル相関性")
        report_lines.append("   - 為替変動の地域需給への影響")
        report_lines.append("")
        report_lines.append("5. 実践的スプレッド戦略:")
        report_lines.append("   - 金属別スプレッド方向予測（コンタンゴ/バックワーデーション）")
        report_lines.append("   - 期間構造変化の具体的時期予想")
        report_lines.append("   - リスク管理を含む具体的ポジション戦略")
        report_lines.append("   - ストップロス・利確レベルの提案")
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report(self, report_content: str, filename: str = None) -> str:
        """レポートをファイルに保存"""
        if filename is None:
            filename = f"Enhanced_Refinitiv_Spread_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"改良版レポート保存完了: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"レポート保存エラー: {e}")
            raise

def main():
    """メイン実行関数"""
    try:
        reporter = EnhancedRefinitivWebClaudeReporter()
        
        print("🚀 改良版Web版Claude用 Refinitivデータレポート生成")
        print("=" * 60)
        print("• LME在庫: オンワラント・キャンセルワラント分解")
        print("• ニュース: 本文取得機能付き")  
        print("• マクロ指標: 確実なRICでの週次トレンド分析")
        print("=" * 60)
        
        # レポート生成
        report_content = reporter.generate_enhanced_web_claude_report()
        
        # ファイル保存
        saved_filename = reporter.save_report(report_content)
        
        print(f"\n✅ 改良版レポート生成完了!")
        print(f"📄 保存ファイル: {saved_filename}")
        print(f"📊 ファイルサイズ: {len(report_content.encode('utf-8')):,} bytes")
        print("\n🔗 このファイルをWeb版Claudeにアップロードして詳細分析を依頼してください。")
        print("💡 改良点: ワラント分解、ニュース本文、確実なマクロ指標")
        
        return 0
        
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())