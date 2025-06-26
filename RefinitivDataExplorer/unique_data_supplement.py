#!/usr/bin/env python3
"""
Unique Data Supplement for LME Daily Report
既存のDaily Reportに載っていない項目のみを取得するスプレッド予測補完システム

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

class UniqueDataSupplement:
    """Daily Reportに無い項目のみの補完データ取得器"""
    
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
        logger = logging.getLogger('UniqueDataSupplement')
        logger.setLevel(logging.INFO)
        
        # コンソール出力
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def get_warrant_status_breakdown(self) -> Dict[str, Any]:
        """LME在庫のワラント状況詳細（Daily Reportに無い項目）"""
        self.logger.info("ワラント状況詳細取得開始...")
        
        warrant_data = {
            "timestamp": datetime.now().isoformat(),
            "warrant_breakdown": {},
            "errors": []
        }
        
        # Daily Reportには総在庫のみ。ワラント分解データは未収録
        warrant_rics = {
            "copper": {
                "live_warrants": "LMCAW=",
                "cancelled_warrants": "LMCACN=", 
                "on_warrant": "LMCAON=",
                "warehouse_stocks": "0#LME-CU-WH"
            },
            "aluminum": {
                "live_warrants": "LMALW=",
                "cancelled_warrants": "LMALCN=",
                "on_warrant": "LMALON=", 
                "warehouse_stocks": "0#LME-AL-WH"
            }
        }
        
        for metal, rics in warrant_rics.items():
            self.logger.info(f"{metal}ワラント詳細取得中...")
            warrant_data["warrant_breakdown"][metal] = {}
            
            for warrant_type, ric in rics.items():
                try:
                    data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    
                    if data is not None and not data.empty:
                        row = data.iloc[0]
                        value = row.get('CF_LAST')
                        
                        if pd.notna(value) and value is not None:
                            warrant_data["warrant_breakdown"][metal][warrant_type] = {
                                "value": float(value),
                                "date": str(row.get('CF_DATE', 'N/A')),
                                "ric": ric,
                                "significance": self._get_warrant_significance(warrant_type)
                            }
                            self.logger.info(f"✅ {metal} {warrant_type}: {value}")
                        else:
                            self.logger.warning(f"⚠️  {metal} {warrant_type} データ空")
                    else:
                        self.logger.warning(f"⚠️  {metal} {warrant_type} アクセス失敗: {ric}")
                        if err:
                            warrant_data["errors"].append(f"{ric}: {err}")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    error_msg = f"{metal} {warrant_type} ({ric}): {str(e)}"
                    warrant_data["errors"].append(error_msg)
                    self.logger.error(f"❌ {error_msg}")
            
            time.sleep(0.5)
        
        return warrant_data
    
    def _get_warrant_significance(self, warrant_type: str) -> str:
        """ワラント種別の意義説明"""
        significance_map = {
            "live_warrants": "Live Warrant = 即座に出庫可能在庫（バックワーデーション要因）",
            "cancelled_warrants": "Cancelled Warrant = 出庫予約済み在庫（タイト感の先行指標）", 
            "on_warrant": "On Warrant = 公式倉庫在庫総量",
            "warehouse_stocks": "Warehouse Breakdown = 倉庫別在庫分布"
        }
        return significance_map.get(warrant_type, "在庫詳細情報")
    
    def get_cftc_positioning_data(self) -> Dict[str, Any]:
        """CFTC建玉明細（Daily Reportに無い項目）"""
        self.logger.info("CFTC建玉明細取得開始...")
        
        cftc_data = {
            "timestamp": datetime.now().isoformat(),
            "positioning": {},
            "errors": []
        }
        
        # Daily Reportには含まれていないCFTCポジション詳細
        cftc_rics = {
            "copper_futures": {
                "commercial_long": "CFTCCUCOM.L",
                "commercial_short": "CFTCCUCOM.S", 
                "managed_money_long": "CFTCCUMM.L",
                "managed_money_short": "CFTCCUMM.S",
                "reportable_long": "CFTCCUREP.L",
                "reportable_short": "CFTCCUREP.S"
            }
        }
        
        for market, rics in cftc_rics.items():
            self.logger.info(f"{market} CFTC建玉取得中...")
            cftc_data["positioning"][market] = {}
            
            for position_type, ric in rics.items():
                try:
                    data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    
                    if data is not None and not data.empty:
                        row = data.iloc[0]
                        value = row.get('CF_LAST')
                        
                        if pd.notna(value) and value is not None:
                            cftc_data["positioning"][market][position_type] = {
                                "contracts": int(value) if value > 0 else 0,
                                "date": str(row.get('CF_DATE', 'N/A')),
                                "ric": ric
                            }
                            self.logger.info(f"✅ {market} {position_type}: {value} contracts")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    error_msg = f"{market} {position_type} ({ric}): {str(e)}"
                    cftc_data["errors"].append(error_msg)
                    self.logger.debug(f"⚠️  {error_msg}")
            
            # ネットポジション計算
            if market in cftc_data["positioning"]:
                try:
                    mm_long = cftc_data["positioning"][market].get("managed_money_long", {}).get("contracts", 0)
                    mm_short = cftc_data["positioning"][market].get("managed_money_short", {}).get("contracts", 0)
                    
                    if mm_long > 0 and mm_short > 0:
                        net_position = mm_long - mm_short
                        cftc_data["positioning"][market]["managed_money_net"] = {
                            "contracts": net_position,
                            "significance": "正=投機筋買い越し（強気）, 負=売り越し（弱気）"
                        }
                        self.logger.info(f"✅ {market} MM Net: {net_position} contracts")
                except:
                    pass
        
        return cftc_data
    
    def get_options_market_data(self) -> Dict[str, Any]:
        """オプション市場データ（Daily Reportに無い項目）"""
        self.logger.info("オプション市場データ取得開始...")
        
        options_data = {
            "timestamp": datetime.now().isoformat(),
            "implied_volatility": {},
            "put_call_ratio": {},
            "errors": []
        }
        
        # Daily Reportには含まれていないオプション詳細
        option_rics = {
            "copper": {
                "atm_iv": "CMCUATM=IV",
                "iv_skew": "CMCUSKEW=", 
                "put_call_ratio": "CMCUPCR=",
                "delta_hedge": "CMCUDELTA="
            },
            "aluminum": {
                "atm_iv": "CMALATM=IV",
                "iv_skew": "CMALSKEW=",
                "put_call_ratio": "CMALPCR=", 
                "delta_hedge": "CMALDELTA="
            }
        }
        
        for metal, rics in option_rics.items():
            self.logger.info(f"{metal}オプション詳細取得中...")
            options_data["implied_volatility"][metal] = {}
            
            for option_type, ric in rics.items():
                try:
                    data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                    
                    if data is not None and not data.empty:
                        row = data.iloc[0]
                        value = row.get('CF_LAST')
                        
                        if pd.notna(value) and value is not None:
                            options_data["implied_volatility"][metal][option_type] = {
                                "value": float(value),
                                "date": str(row.get('CF_DATE', 'N/A')),
                                "ric": ric,
                                "interpretation": self._get_option_interpretation(option_type, value)
                            }
                            self.logger.info(f"✅ {metal} {option_type}: {value}")
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    error_msg = f"{metal} {option_type} ({ric}): {str(e)}"
                    options_data["errors"].append(error_msg)
                    self.logger.debug(f"⚠️  {error_msg}")
        
        return options_data
    
    def _get_option_interpretation(self, option_type: str, value: float) -> str:
        """オプション指標の解釈"""
        if option_type == "atm_iv":
            if value > 30:
                return f"高ボラティリティ({value:.1f}%) - 市場不安定"
            elif value < 15:
                return f"低ボラティリティ({value:.1f}%) - 市場安定"
            else:
                return f"中程度ボラティリティ({value:.1f}%)"
        elif option_type == "put_call_ratio":
            if value > 1.2:
                return f"プット優勢({value:.2f}) - 弱気センチメント"
            elif value < 0.8:
                return f"コール優勢({value:.2f}) - 強気センチメント"
            else:
                return f"中立({value:.2f})"
        return f"値: {value}"
    
    def get_baltic_shipping_details(self) -> Dict[str, Any]:
        """バルチック指数詳細（Daily Reportの簡単な説明を詳細化）"""
        self.logger.info("バルチック指数詳細取得開始...")
        
        baltic_data = {
            "timestamp": datetime.now().isoformat(),
            "shipping_rates": {},
            "route_breakdown": {},
            "errors": []
        }
        
        # Daily Reportにはバルチック指数の概要のみ。詳細は未収録
        baltic_rics = {
            "overall": ".BADI",
            "capesize": ".BACI", 
            "panamax": ".BAPI",
            "supramax": ".BASI",
            "handysize": ".BHSI"
        }
        
        route_rics = {
            "pacific_iron_ore": ".BATCI4",  # Pacific iron ore routes
            "atlantic_iron_ore": ".BATCI5", # Atlantic iron ore routes  
            "pacific_coal": ".BATCI6",      # Pacific coal routes
            "grains": ".BATCI7"             # Grains routes
        }
        
        # 船舶サイズ別レート
        for ship_type, ric in baltic_rics.items():
            try:
                data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME', 'PCTCHNG'])
                
                if data is not None and not data.empty:
                    row = data.iloc[0]
                    value = row.get('CF_LAST')
                    change = row.get('PCTCHNG')
                    
                    if pd.notna(value):
                        baltic_data["shipping_rates"][ship_type] = {
                            "index_value": float(value),
                            "daily_change_pct": float(change) if pd.notna(change) else None,
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "name": str(row.get('CF_NAME', ship_type)),
                            "significance": self._get_ship_significance(ship_type)
                        }
                        self.logger.info(f"✅ {ship_type}: {value}")
                
                time.sleep(0.3)
                
            except Exception as e:
                error_msg = f"{ship_type} ({ric}): {str(e)}"
                baltic_data["errors"].append(error_msg)
                self.logger.debug(f"⚠️  {error_msg}")
        
        # 航路別詳細
        for route_type, ric in route_rics.items():
            try:
                data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE', 'CF_NAME'])
                
                if data is not None and not data.empty:
                    row = data.iloc[0]
                    value = row.get('CF_LAST')
                    
                    if pd.notna(value):
                        baltic_data["route_breakdown"][route_type] = {
                            "rate": float(value),
                            "date": str(row.get('CF_DATE', 'N/A')),
                            "route_description": self._get_route_description(route_type)
                        }
                        self.logger.info(f"✅ {route_type}: {value}")
                
                time.sleep(0.3)
                
            except Exception as e:
                baltic_data["errors"].append(f"{route_type}: {str(e)}")
        
        return baltic_data
    
    def _get_ship_significance(self, ship_type: str) -> str:
        """船舶タイプの意義説明"""
        significance_map = {
            "overall": "総合指数 - 全船舶タイプの加重平均",
            "capesize": "大型船(180k+ DWT) - 鉄鉱石・石炭輸送主体", 
            "panamax": "中型船(65-90k DWT) - 穀物・石炭輸送",
            "supramax": "中小型船(50-65k DWT) - 多様貨物対応",
            "handysize": "小型船(15-35k DWT) - 近距離・小口輸送"
        }
        return significance_map.get(ship_type, "海運レート指標")
    
    def _get_route_description(self, route_type: str) -> str:
        """航路の説明"""
        route_map = {
            "pacific_iron_ore": "太平洋鉄鉱石航路 - 豪州→中国・日本",
            "atlantic_iron_ore": "大西洋鉄鉱石航路 - ブラジル→欧州・中国", 
            "pacific_coal": "太平洋石炭航路 - 豪州・インドネシア→アジア",
            "grains": "穀物航路 - 米国・南米→アジア・欧州"
        }
        return route_map.get(route_type, "海運航路")
    
    def get_forward_curve_analysis(self) -> Dict[str, Any]:
        """フォワードカーブ詳細分析（Daily Reportより詳細）"""
        self.logger.info("フォワードカーブ詳細分析開始...")
        
        curve_data = {
            "timestamp": datetime.now().isoformat(),
            "curve_shape": {},
            "contango_backwardation": {},
            "errors": []
        }
        
        # Daily Reportには一部期間のカーブのみ。全期間構造は未収録
        metals = ["copper", "aluminum", "zinc", "lead", "nickel", "tin"]
        
        for metal in metals:
            self.logger.info(f"{metal}カーブ構造分析中...")
            
            # 3ヶ月〜24ヶ月の主要限月
            ric_pattern = f"CM{metal.upper()[:2]}U" if metal != "aluminum" else "CMAL"
            
            periods = {
                "3m": "3",
                "6m": "M", 
                "12m": "3",  # 翌年3月
                "15m": "M",  # 翌年6月
                "24m": "3"   # 2年後3月
            }
            
            curve_prices = {}
            
            for period, month_code in periods.items():
                try:
                    year_suffix = "25" if period in ["3m", "6m"] else "26"
                    if period in ["24m"]:
                        year_suffix = "27"
                    
                    ric = f"{ric_pattern}{month_code}{year_suffix}"
                    
                    data, err = ek.get_data(ric, ['CF_LAST', 'CF_DATE'])
                    
                    if data is not None and not data.empty:
                        row = data.iloc[0]
                        price = row.get('CF_LAST')
                        
                        if pd.notna(price):
                            curve_prices[period] = {
                                "price": float(price),
                                "ric": ric,
                                "date": str(row.get('CF_DATE', 'N/A'))
                            }
                            self.logger.info(f"✅ {metal} {period}: ${price}")
                    
                    time.sleep(0.2)
                    
                except Exception as e:
                    curve_data["errors"].append(f"{metal} {period}: {str(e)}")
            
            # カーブ形状分析
            if len(curve_prices) >= 3:
                curve_data["curve_shape"][metal] = self._analyze_curve_shape(curve_prices)
                curve_data["contango_backwardation"][metal] = self._analyze_contango_backwardation(curve_prices)
        
        return curve_data
    
    def _analyze_curve_shape(self, prices: Dict) -> Dict:
        """カーブ形状分析"""
        if "3m" not in prices or "24m" not in prices:
            return {"shape": "insufficient_data"}
        
        front_price = prices["3m"]["price"]
        back_price = prices["24m"]["price"]
        
        total_slope = (back_price - front_price) / front_price * 100
        
        shape_analysis = {
            "front_to_back_slope_pct": round(total_slope, 2),
            "shape_description": "",
            "market_implication": ""
        }
        
        if total_slope > 5:
            shape_analysis["shape_description"] = "Steep Contango"
            shape_analysis["market_implication"] = "供給過剰・金利コスト高・需要弱含み"
        elif total_slope > 1:
            shape_analysis["shape_description"] = "Moderate Contango" 
            shape_analysis["market_implication"] = "緩やかな供給過剰・正常なCarry Cost"
        elif total_slope < -5:
            shape_analysis["shape_description"] = "Steep Backwardation"
            shape_analysis["market_implication"] = "現物タイト・緊急需要・供給不安"
        elif total_slope < -1:
            shape_analysis["shape_description"] = "Moderate Backwardation"
            shape_analysis["market_implication"] = "現物やや不足・需要堅調"
        else:
            shape_analysis["shape_description"] = "Flat/Neutral"
            shape_analysis["market_implication"] = "需給均衡・中立的市場"
        
        return shape_analysis
    
    def _analyze_contango_backwardation(self, prices: Dict) -> Dict:
        """コンタンゴ・バックワーデーション分析"""
        analysis = {
            "near_far_spreads": {},
            "carry_cost_analysis": {}
        }
        
        # 近限-遠限スプレッド
        if "3m" in prices and "6m" in prices:
            front = prices["3m"]["price"]
            next_front = prices["6m"]["price"]
            spread_3_6 = next_front - front
            
            analysis["near_far_spreads"]["3m_6m_spread"] = {
                "spread_value": round(spread_3_6, 2),
                "spread_pct": round(spread_3_6 / front * 100, 2),
                "annualized_rate": round((spread_3_6 / front) * 4 * 100, 2)  # 3ヶ月→年率
            }
        
        return analysis
    
    def generate_unique_supplement_report(self) -> str:
        """Daily Report補完用レポート生成"""
        self.logger.info("Daily Report補完レポート生成開始...")
        
        # 各カテゴリーのユニークデータ取得
        warrant_data = self.get_warrant_status_breakdown()
        cftc_data = self.get_cftc_positioning_data()
        options_data = self.get_options_market_data()
        baltic_data = self.get_baltic_shipping_details()
        curve_data = self.get_forward_curve_analysis()
        
        # レポート生成
        report_lines = []
        
        # ヘッダー
        report_lines.append("=" * 80)
        report_lines.append("【Web版Claude用】Daily Report補完データ - スプレッド予測特化")
        report_lines.append("=" * 80)
        report_lines.append(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        report_lines.append("データソース: Refinitiv EIKON API（Daily Report未収録項目のみ）")
        report_lines.append("")
        report_lines.append("【重要】このレポートは既存のDaily Reportと併用することで、")
        report_lines.append("スプレッド予測精度を大幅に向上させる専門的補完データです。")
        report_lines.append("")
        
        # プロンプト
        report_lines.append("【Claude分析用プロンプト】")
        report_lines.append("既存のLME Daily Reportと以下の補完データを統合して、")
        report_lines.append("LME金属先物スプレッド（コンタンゴ/バックワーデーション）の")
        report_lines.append("高精度予測分析を実施してください。")
        report_lines.append("")
        
        # 1. ワラント詳細分解
        report_lines.append("=" * 60)
        report_lines.append("【補完データ1】LME在庫ワラント詳細分解")
        report_lines.append("=" * 60)
        report_lines.append("※Daily Reportには総在庫のみ。以下は内部構造分解")
        report_lines.append("")
        
        if "warrant_breakdown" in warrant_data:
            for metal, breakdown in warrant_data["warrant_breakdown"].items():
                if breakdown:
                    report_lines.append(f"--- {metal.upper()}ワラント構造 ---")
                    for warrant_type, data in breakdown.items():
                        value = data.get("value", "N/A")
                        date = data.get("date", "N/A")
                        significance = data.get("significance", "")
                        report_lines.append(f"  {warrant_type}: {value} トン (更新: {date})")
                        if significance:
                            report_lines.append(f"    → {significance}")
                    report_lines.append("")
        
        # 2. CFTC建玉明細
        report_lines.append("=" * 60)
        report_lines.append("【補完データ2】CFTC建玉明細（投機筋ポジション）")
        report_lines.append("=" * 60)
        report_lines.append("※Daily Reportには含まれない詳細ポジション分析")
        report_lines.append("")
        
        if "positioning" in cftc_data:
            for market, positions in cftc_data["positioning"].items():
                if positions:
                    report_lines.append(f"--- {market.upper()}建玉状況 ---")
                    for position_type, data in positions.items():
                        if "contracts" in data:
                            contracts = data.get("contracts", 0)
                            date = data.get("date", "N/A")
                            report_lines.append(f"  {position_type}: {contracts:,} contracts (更新: {date})")
                        elif "significance" in data:
                            significance = data.get("significance", "")
                            contracts = data.get("contracts", 0)
                            report_lines.append(f"  {position_type}: {contracts:,} contracts")
                            report_lines.append(f"    → {significance}")
                    report_lines.append("")
        
        # 3. オプション市場データ
        report_lines.append("=" * 60)
        report_lines.append("【補完データ3】オプション市場分析")
        report_lines.append("=" * 60)
        report_lines.append("※Daily Reportには含まれないボラティリティ・リスク分析")
        report_lines.append("")
        
        if "implied_volatility" in options_data:
            for metal, iv_data in options_data["implied_volatility"].items():
                if iv_data:
                    report_lines.append(f"--- {metal.upper()}オプション市場 ---")
                    for option_type, data in iv_data.items():
                        value = data.get("value", "N/A")
                        interpretation = data.get("interpretation", "")
                        date = data.get("date", "N/A")
                        report_lines.append(f"  {option_type}: {value} (更新: {date})")
                        if interpretation:
                            report_lines.append(f"    → {interpretation}")
                    report_lines.append("")
        
        # 4. バルチック指数詳細
        report_lines.append("=" * 60)
        report_lines.append("【補完データ4】バルチック指数詳細分解")
        report_lines.append("=" * 60)
        report_lines.append("※Daily Reportには総合指数のみ。以下は船舶別・航路別詳細")
        report_lines.append("")
        
        if "shipping_rates" in baltic_data:
            report_lines.append("--- 船舶タイプ別レート ---")
            for ship_type, data in baltic_data["shipping_rates"].items():
                value = data.get("index_value", "N/A")
                change = data.get("daily_change_pct", "N/A")
                significance = data.get("significance", "")
                report_lines.append(f"  {ship_type}: {value}")
                if change != "N/A":
                    report_lines.append(f"    日次変動: {change:+.2f}%")
                if significance:
                    report_lines.append(f"    → {significance}")
            report_lines.append("")
        
        if "route_breakdown" in baltic_data:
            report_lines.append("--- 主要航路レート ---")
            for route, data in baltic_data["route_breakdown"].items():
                rate = data.get("rate", "N/A")
                description = data.get("route_description", "")
                report_lines.append(f"  {route}: {rate}")
                if description:
                    report_lines.append(f"    → {description}")
            report_lines.append("")
        
        # 5. フォワードカーブ詳細
        report_lines.append("=" * 60)
        report_lines.append("【補完データ5】フォワードカーブ詳細分析")
        report_lines.append("=" * 60)
        report_lines.append("※Daily Reportより詳細な期間構造・スプレッド分析")
        report_lines.append("")
        
        if "curve_shape" in curve_data:
            for metal, shape_analysis in curve_data["curve_shape"].items():
                if shape_analysis and "shape_description" in shape_analysis:
                    report_lines.append(f"--- {metal.upper()}カーブ形状 ---")
                    slope = shape_analysis.get("front_to_back_slope_pct", "N/A")
                    shape = shape_analysis.get("shape_description", "N/A")
                    implication = shape_analysis.get("market_implication", "")
                    
                    report_lines.append(f"  フロント-バック勾配: {slope}%")
                    report_lines.append(f"  カーブ形状: {shape}")
                    if implication:
                        report_lines.append(f"  市場含意: {implication}")
                    report_lines.append("")
        
        # エラーサマリー
        all_errors = []
        all_errors.extend(warrant_data.get("errors", []))
        all_errors.extend(cftc_data.get("errors", []))
        all_errors.extend(options_data.get("errors", []))
        all_errors.extend(baltic_data.get("errors", []))
        all_errors.extend(curve_data.get("errors", []))
        
        if all_errors:
            report_lines.append("--- データ取得制限事項 ---")
            for error in all_errors[:8]:
                report_lines.append(f"  • {error}")
            report_lines.append("")
        
        # 統合分析指示
        report_lines.append("=" * 80)
        report_lines.append("【統合分析指示】Daily Report + 補完データ")
        report_lines.append("=" * 80)
        report_lines.append("")
        report_lines.append("以下の手順で統合スプレッド分析を実施してください：")
        report_lines.append("")
        report_lines.append("1. ワラント構造 × 価格データ:")
        report_lines.append("   - キャンセルワラント比率とバックワーデーション相関")
        report_lines.append("   - Live Warrant減少による現物タイト化予測")
        report_lines.append("")
        report_lines.append("2. CFTC建玉 × 在庫データ:")
        report_lines.append("   - 投機筋Net Position方向と在庫トレンド整合性")
        report_lines.append("   - Commercial vs Managed Money の力関係")
        report_lines.append("")
        report_lines.append("3. オプションIV × 価格ボラティリティ:")
        report_lines.append("   - IV上昇とスプレッド変動拡大の関係")
        report_lines.append("   - Put/Call比率による方向性バイアス")
        report_lines.append("")
        report_lines.append("4. バルチック詳細 × 物流コスト:")
        report_lines.append("   - 船舶タイプ別レート上昇のCarry Cost影響")
        report_lines.append("   - 航路別混雑による地域プレミアム変動")
        report_lines.append("")
        report_lines.append("5. カーブ形状 × マクロ環境:")
        report_lines.append("   - 金利変動とContango/Backwardation構造")
        report_lines.append("   - 期間構造変化の具体的時期とトリガー予測")
        report_lines.append("")
        report_lines.append("【最終出力要求】")
        report_lines.append("- 金属別スプレッド方向予測（1-2週間、1-3ヶ月）")
        report_lines.append("- 具体的エントリー・エグジット戦略")
        report_lines.append("- リスクシナリオと管理方法")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def save_report(self, report_content: str, filename: str = None) -> str:
        """レポート保存"""
        if filename is None:
            filename = f"Daily_Report_Supplement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"補完レポート保存完了: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"レポート保存エラー: {e}")
            raise

def main():
    """メイン実行関数"""
    try:
        supplement = UniqueDataSupplement()
        
        print("📊 Daily Report補完データシステム")
        print("=" * 50)
        print("既存レポートに無い項目のみを取得:")
        print("• LME在庫ワラント詳細分解")
        print("• CFTC建玉明細（投機筋ポジション）")
        print("• オプション市場データ（IV・P/C比率）")
        print("• バルチック指数詳細分解")
        print("• フォワードカーブ詳細分析")
        print("=" * 50)
        
        # 補完レポート生成
        report_content = supplement.generate_unique_supplement_report()
        
        # ファイル保存
        saved_filename = supplement.save_report(report_content)
        
        print(f"\n✅ Daily Report補完データ生成完了!")
        print(f"📄 保存ファイル: {saved_filename}")
        print(f"📊 ファイルサイズ: {len(report_content.encode('utf-8')):,} bytes")
        print("\n🔗 既存のDaily Reportと併用してWeb版Claudeで分析してください。")
        print("💡 補完内容: Daily Reportに無いスプレッド予測特化データ")
        
        return 0
        
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())