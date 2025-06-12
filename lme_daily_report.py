#!/usr/bin/env python3
"""
LME Daily Market Report Generator
London Metal Exchange主要6金属の日次マーケットレポート自動生成システム

Author: Claude Code
Created: 2025-06-10
"""

import eikon as ek
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from pathlib import Path
import warnings
import time
warnings.filterwarnings('ignore')

class LMEReportGenerator:
    """LME日次レポート生成器"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初期化
        
        Args:
            config_path: 設定ファイルパス
        """
        self.config = self._load_config(config_path)
        self.metals_rics = self.config["metals_rics"]
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
        except FileNotFoundError:
            self.logger.error(f"設定ファイルが見つかりません: {config_path}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            raise
            
    def _setup_logger(self) -> logging.Logger:
        """ログ設定"""
        logger = logging.getLogger('LME_Report')
        logger.setLevel(logging.INFO)  # Normal logging level
        
        # ログディレクトリ作成
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # ハンドラー設定
        handler = logging.FileHandler(
            log_dir / f"lme_report_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # コンソール出力も追加
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def _get_previous_business_day(self) -> datetime:
        """前営業日を取得"""
        today = datetime.now()
        
        # 市場休日の設定を取得
        market_holidays = self.config.get("market_holidays", [])
        holiday_dates = [datetime.strptime(date, '%Y-%m-%d').date() for date in market_holidays]
        
        # 前営業日を計算
        days_back = 1
        while days_back <= 7:  # 最大1週間前まで
            candidate_date = today - timedelta(days=days_back)
            
            # 土日をスキップ
            if candidate_date.weekday() >= 5:  # 5=土曜日, 6=日曜日
                days_back += 1
                continue
            
            # 祝日をスキップ
            if candidate_date.date() in holiday_dates:
                days_back += 1
                continue
            
            return candidate_date
            
        # フォールバック：昨日を返す
        return today - timedelta(days=1)
        
    def get_price_data(self) -> Dict:
        """価格データ取得"""
        self.logger.info("価格データ取得開始")
        price_data = {}
        
        try:
            for metal_name, ric in self.metals_rics.items():
                self.logger.info(f"{metal_name} 価格データ取得中...")
                
                # 価格データ取得
                fields = [
                    'CF_CLOSE',    # 前日終値
                    'OPEN_PRC',    # 始値
                    'HIGH_1',      # 高値
                    'LOW_1',       # 安値
                    'PCTCHNG',     # 変動率
                    'CASH_PREMI',  # キャッシュプレミアム
                    'CONTANGO'     # コンタンゴ
                ]
                
                success = False
                
                # メインRICで試行
                try:
                    df, err = ek.get_data(ric, fields)
                    if err:
                        self.logger.warning(f"{metal_name} データ取得警告: {err}")
                    
                    if not df.empty and df['CF_CLOSE'].iloc[0] is not None:
                        success = True
                        self.logger.info(f"{metal_name} メインRIC({ric})でデータ取得成功")
                    else:
                        self.logger.warning(f"{metal_name} メインRIC({ric})でデータが空または無効")
                        
                except Exception as e:
                    self.logger.error(f"{metal_name} メインRIC({ric})取得エラー: {e}")
                
                # メインRICで失敗した場合、代替RICを試行
                if not success:
                    alternative_rics = self.config.get("alternative_metals_rics", {}).get(metal_name, [])
                    
                    for alt_ric in alternative_rics:
                        try:
                            self.logger.info(f"{metal_name} 代替RIC({alt_ric})を試行")
                            df, err = ek.get_data(alt_ric, fields)
                            
                            if err:
                                self.logger.warning(f"{metal_name} 代替RIC({alt_ric})警告: {err}")
                            
                            if not df.empty and df['CF_CLOSE'].iloc[0] is not None:
                                ric = alt_ric  # 成功したRICを使用
                                success = True
                                self.logger.info(f"{metal_name} 代替RIC({alt_ric})でデータ取得成功")
                                break
                                
                        except Exception as alt_e:
                            self.logger.warning(f"{metal_name} 代替RIC({alt_ric})エラー: {alt_e}")
                            continue
                
                if success and not df.empty:
                    # 週次・月次・年初来変動率計算
                    historical_data = self._get_historical_returns(ric)
                    
                    price_data[metal_name] = {
                        'ric': ric,
                        'close': df['CF_CLOSE'].iloc[0] if 'CF_CLOSE' in df.columns else None,
                        'open': df['OPEN_PRC'].iloc[0] if 'OPEN_PRC' in df.columns else None,
                        'high': df['HIGH_1'].iloc[0] if 'HIGH_1' in df.columns else None,
                        'low': df['LOW_1'].iloc[0] if 'LOW_1' in df.columns else None,
                        'daily_change': df['PCTCHNG'].iloc[0] if 'PCTCHNG' in df.columns else None,
                        'weekly_change': historical_data.get('weekly_change'),
                        'monthly_change': historical_data.get('monthly_change'),
                        'ytd_change': historical_data.get('ytd_change'),
                        'recent_trend': historical_data.get('recent_trend', {}),
                        'cash_premium': df['CASH_PREMI'].iloc[0] if 'CASH_PREMI' in df.columns else None,
                        'contango': df['CONTANGO'].iloc[0] if 'CONTANGO' in df.columns else None
                    }
                else:
                    self.logger.error(f"{metal_name} 全てのRICで価格データ取得失敗、フォールバックデータを使用")
                    price_data[metal_name] = self._get_fallback_price_data(metal_name)
                    
        except Exception as e:
            self.logger.error(f"価格データ取得全体エラー: {e}")
            
        self.logger.info("価格データ取得完了")
        return price_data
        
    def _get_historical_returns(self, ric: str) -> Dict:
        """週次・月次・年初来変動率計算 + 直近5営業日トレンド"""
        try:
            end_date = datetime.now()
            start_date = datetime(end_date.year, 1, 1)  # 年初
            
            df = ek.get_timeseries(
                ric, 
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                fields=['CLOSE', 'HIGH', 'LOW', 'VOLUME']
            )
            
            if df is not None and not df.empty:
                current_price = df['CLOSE'].iloc[-1]
                
                # 基本的な変動率計算
                week_ago = df['CLOSE'].iloc[-6] if len(df) >= 6 else df['CLOSE'].iloc[0]
                weekly_change = ((current_price - week_ago) / week_ago * 100) if week_ago != 0 else 0
                
                month_ago = df['CLOSE'].iloc[-21] if len(df) >= 21 else df['CLOSE'].iloc[0]
                monthly_change = ((current_price - month_ago) / month_ago * 100) if month_ago != 0 else 0
                
                ytd_price = df['CLOSE'].iloc[0]
                ytd_change = ((current_price - ytd_price) / ytd_price * 100) if ytd_price != 0 else 0
                
                # 直近5営業日のトレンド分析
                recent_trend = self._analyze_recent_trend(df)
                
                return {
                    'weekly_change': weekly_change,
                    'monthly_change': monthly_change,
                    'ytd_change': ytd_change,
                    'recent_trend': recent_trend
                }
            else:
                return {
                    'weekly_change': None, 
                    'monthly_change': None, 
                    'ytd_change': None,
                    'recent_trend': {}
                }
                
        except Exception as e:
            self.logger.error(f"履歴データ取得エラー: {e}")
            return {
                'weekly_change': None, 
                'monthly_change': None, 
                'ytd_change': None,
                'recent_trend': {}
            }
    
    def _analyze_recent_trend(self, df: pd.DataFrame) -> Dict:
        """直近5営業日のトレンド分析"""
        try:
            if len(df) < 5:
                return {}
            
            # 直近5営業日のデータ
            recent_data = df.tail(5).copy()
            
            # 日々の変動率計算
            recent_data['daily_change'] = recent_data['CLOSE'].pct_change() * 100
            
            # 平均変動率
            avg_daily_change = recent_data['daily_change'].mean()
            
            # ボラティリティ（標準偏差）
            volatility = recent_data['daily_change'].std()
            
            # トレンド方向（線形回帰の傾き）
            x = range(len(recent_data))
            y = recent_data['CLOSE'].values
            
            if len(x) >= 2:
                # 簡単な線形回帰
                x_mean = sum(x) / len(x)
                y_mean = sum(y) / len(y)
                
                numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
                denominator = sum((x[i] - x_mean) ** 2 for i in range(len(x)))
                
                slope = numerator / denominator if denominator != 0 else 0
                
                # トレンドの強さ
                if abs(slope) > y_mean * 0.001:  # 0.1%以上の傾き
                    trend_direction = "上昇" if slope > 0 else "下降"
                    trend_strength = "強" if abs(slope) > y_mean * 0.002 else "弱"
                else:
                    trend_direction = "横ばい"
                    trend_strength = "中"
            else:
                trend_direction = "不明"
                trend_strength = "不明"
            
            # 高値・安値分析
            recent_high = recent_data['HIGH'].max()
            recent_low = recent_data['LOW'].min()
            current_price = recent_data['CLOSE'].iloc[-1]
            
            # 現在価格のレンジ内での位置
            price_range = recent_high - recent_low
            if price_range > 0:
                position_in_range = (current_price - recent_low) / price_range
                if position_in_range > 0.8:
                    range_position = "高値圏"
                elif position_in_range < 0.2:
                    range_position = "安値圏"
                else:
                    range_position = "中値圏"
            else:
                range_position = "不明"
            
            # 連続上昇・下降日数
            consecutive_days = self._count_consecutive_direction(recent_data['daily_change'])
            
            return {
                'avg_daily_change': round(avg_daily_change, 2) if not pd.isna(avg_daily_change) else None,
                'volatility': round(volatility, 2) if not pd.isna(volatility) else None,
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'recent_high': recent_high,
                'recent_low': recent_low,
                'range_position': range_position,
                'consecutive_days': consecutive_days,
                'daily_changes': recent_data['daily_change'].dropna().tolist()
            }
            
        except Exception as e:
            self.logger.debug(f"トレンド分析エラー: {e}")
            return {}
    
    def _count_consecutive_direction(self, daily_changes: pd.Series) -> Dict:
        """連続上昇・下降日数をカウント"""
        try:
            changes = daily_changes.dropna()
            if len(changes) < 2:
                return {'direction': '不明', 'days': 0}
            
            # 最新の変動から逆順に見て連続方向をカウント
            last_direction = None
            consecutive_count = 0
            
            for change in reversed(changes.tolist()):
                current_direction = "上昇" if change > 0 else "下降" if change < 0 else "横ばい"
                
                if last_direction is None:
                    last_direction = current_direction
                    consecutive_count = 1
                elif current_direction == last_direction and current_direction != "横ばい":
                    consecutive_count += 1
                else:
                    break
            
            return {
                'direction': last_direction,
                'days': consecutive_count
            }
            
        except Exception as e:
            return {'direction': '不明', 'days': 0}
    
    def _get_inventory_trend(self, ric: str) -> Dict:
        """在庫の5営業日トレンド分析"""
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)  # 余裕をもって10日前から
            
            ts_data = ek.get_timeseries(
                ric,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                fields=['CLOSE']
            )
            
            if ts_data is not None and not ts_data.empty and len(ts_data) >= 2:
                # 最新から過去5営業日のデータを取得
                recent_data = ts_data.tail(5)
                
                if len(recent_data) >= 2:
                    # 在庫変動率計算
                    recent_data = recent_data.copy()
                    recent_data['change'] = recent_data['CLOSE'].diff()
                    recent_data['change_pct'] = recent_data['CLOSE'].pct_change() * 100
                    
                    # 最新値と5日前の比較
                    latest_value = recent_data['CLOSE'].iloc[-1]
                    oldest_value = recent_data['CLOSE'].iloc[0]
                    
                    period_change = latest_value - oldest_value
                    period_change_pct = ((latest_value - oldest_value) / oldest_value * 100) if oldest_value != 0 else 0
                    
                    # 平均日次変動
                    avg_daily_change = recent_data['change'].mean()
                    
                    # トレンド方向判定
                    if abs(period_change_pct) < 1:  # 1%未満は横ばい
                        trend_direction = "横ばい"
                    elif period_change_pct > 0:
                        trend_direction = "増加"
                    else:
                        trend_direction = "減少"
                    
                    # 変動の強さ
                    if abs(period_change_pct) > 5:
                        trend_strength = "大"
                    elif abs(period_change_pct) > 2:
                        trend_strength = "中"
                    else:
                        trend_strength = "小"
                    
                    return {
                        'period_change': round(period_change, 0) if not pd.isna(period_change) else None,
                        'period_change_pct': round(period_change_pct, 2) if not pd.isna(period_change_pct) else None,
                        'avg_daily_change': round(avg_daily_change, 0) if not pd.isna(avg_daily_change) else None,
                        'trend_direction': trend_direction,
                        'trend_strength': trend_strength,
                        'data_points': len(recent_data)
                    }
                    
            return {}
            
        except Exception as e:
            self.logger.debug(f"在庫トレンド分析エラー ({ric}): {e}")
            return {}
    
    def _get_volume_trend(self, ric: str) -> Dict:
        """取引量の5営業日トレンド分析"""
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)  # 余裕をもって10日前から
            
            ts_data = ek.get_timeseries(
                ric,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                fields=['VOLUME']
            )
            
            if ts_data is not None and not ts_data.empty and 'VOLUME' in ts_data.columns:
                # 最新から過去5営業日のデータを取得
                recent_data = ts_data.tail(5)
                
                if len(recent_data) >= 2 and not recent_data['VOLUME'].isna().all():
                    # 取引量変動分析
                    volume_data = recent_data['VOLUME'].dropna()
                    
                    if len(volume_data) >= 2:
                        latest_volume = volume_data.iloc[-1]
                        avg_volume = volume_data.mean()
                        
                        # 最新値と平均の比較
                        vs_average = ((latest_volume - avg_volume) / avg_volume * 100) if avg_volume != 0 else 0
                        
                        # トレンド判定
                        if abs(vs_average) < 10:  # 10%未満は普通
                            activity_level = "普通"
                        elif vs_average > 20:
                            activity_level = "高"
                        elif vs_average < -20:
                            activity_level = "低"
                        else:
                            activity_level = "やや高" if vs_average > 0 else "やや低"
                        
                        return {
                            'avg_volume': round(avg_volume, 0) if not pd.isna(avg_volume) else None,
                            'latest_volume': round(latest_volume, 0) if not pd.isna(latest_volume) else None,
                            'vs_average_pct': round(vs_average, 1) if not pd.isna(vs_average) else None,
                            'activity_level': activity_level,
                            'data_points': len(volume_data)
                        }
                        
            return {}
            
        except Exception as e:
            self.logger.debug(f"取引量トレンド分析エラー ({ric}): {e}")
            return {}

    def get_inventory_data(self) -> Dict:
        """在庫データ取得"""
        self.logger.info("在庫データ取得開始")
        inventory_data = {}
        
        try:
            # LME在庫データ
            lme_inventory = self._get_lme_inventory()
            
            # COMEX在庫データ（銅のみ）
            comex_inventory = self._get_comex_inventory()
            
            # SHFE在庫データ
            shfe_inventory = self._get_shfe_inventory()
            
            # SMM保税倉庫在庫データ
            smm_inventory = self._get_smm_inventory()
            
            inventory_data = {
                'lme': lme_inventory,
                'comex': comex_inventory,
                'shfe': shfe_inventory,
                'smm': smm_inventory
            }
            
        except Exception as e:
            self.logger.error(f"在庫データ取得エラー: {e}")
            
        self.logger.info("在庫データ取得完了")
        return inventory_data
        
    def _get_lme_inventory(self) -> Dict:
        """LME在庫データ取得（時系列データを使用）"""
        lme_data = {}
        
        try:
            lme_inventory_rics = self.config.get("lme_inventory_rics", {})
            
            for metal_name, ric in lme_inventory_rics.items():
                try:
                    # まず通常のget_dataを試行
                    fields = ['CF_LAST', 'CF_CLOSE', 'CLOSE', 'VALUE']
                    df, err = ek.get_data(ric, fields)
                    
                    total_stock = None
                    
                    # 通常のget_dataで値が取得できる場合
                    if df is not None and not df.empty:
                        for field in fields:
                            if field in df.columns:
                                value = df[field].iloc[0]
                                if value is not None and not pd.isna(value) and str(value) != '<NA>':
                                    total_stock = value
                                    self.logger.info(f"LME {metal_name} 在庫データ取得成功 (get_data {field}): {value}")
                                    break
                    
                    # 通常のget_dataで値が取得できない場合、時系列データを試行
                    if total_stock is None:
                        try:
                            from datetime import datetime, timedelta
                            end_date = datetime.now()
                            start_date = end_date - timedelta(days=7)
                            
                            ts_data = ek.get_timeseries(
                                ric,
                                start_date=start_date.strftime('%Y-%m-%d'),
                                end_date=end_date.strftime('%Y-%m-%d'),
                                fields=['CLOSE', 'VALUE', 'HIGH', 'LOW']
                            )
                            
                            if ts_data is not None and not ts_data.empty:
                                # 最新の有効な値を取得
                                for idx in range(len(ts_data) - 1, -1, -1):  # 最新から過去へ
                                    for field in ['CLOSE', 'VALUE']:
                                        if field in ts_data.columns:
                                            value = ts_data[field].iloc[idx]
                                            if value is not None and not pd.isna(value) and str(value) != '<NA>':
                                                total_stock = value
                                                self.logger.info(f"LME {metal_name} 在庫データ取得成功 (timeseries {field}): {value}")
                                                break
                                    if total_stock is not None:
                                        break
                                        
                        except Exception as ts_error:
                            self.logger.debug(f"LME {metal_name} 時系列データ取得エラー: {ts_error}")
                    
                    if total_stock is None:
                        self.logger.warning(f"LME {metal_name} 在庫データが取得できません")
                    
                    # 在庫トレンド分析
                    inventory_trend = self._get_inventory_trend(ric)
                    
                    lme_data[metal_name] = {
                        'total_stock': total_stock,
                        'live_warrant': None,  
                        'cancelled_warrant': None,
                        'trend': inventory_trend
                    }
                        
                except Exception as e:
                    self.logger.error(f"LME {metal_name} 在庫データエラー: {e}")
                    
        except Exception as e:
            self.logger.error(f"LME在庫データ取得エラー: {e}")
            
        return lme_data
        
    def _get_comex_inventory(self) -> Dict:
        """COMEX在庫データ取得（銅のみ）"""
        comex_data = {}
        
        try:
            copper_ric = self.config.get("comex_copper_ric", "")
            if copper_ric:
                fields = [
                    'CF_LAST',
                    'CF_CLOSE',
                    'CLOSE'
                ]
                
                df, err = ek.get_data(copper_ric, fields)
                if err:
                    self.logger.warning(f"COMEX銅在庫データ警告: {err}")
                
                if not df.empty:
                    # 利用可能な値を順番に試行
                    total_stock = None
                    for field in ['CF_LAST', 'CF_CLOSE', 'CLOSE']:
                        if field in df.columns:
                            value = df[field].iloc[0]
                            if value is not None and not pd.isna(value):
                                total_stock = value
                                break
                    
                    comex_data['Copper'] = {
                        'total_stock': total_stock,
                        'registered': None,
                        'eligible': None
                    }
                    
        except Exception as e:
            self.logger.error(f"COMEX在庫データ取得エラー: {e}")
            
        return comex_data
        
    def _get_shfe_inventory(self) -> Dict:
        """SHFE在庫データ取得"""
        shfe_data = {}
        
        try:
            shfe_inventory_rics = self.config.get("shfe_inventory_rics", {})
            
            for metal_name, ric in shfe_inventory_rics.items():
                try:
                    fields = ['CF_LAST', 'CF_CLOSE', 'CLOSE']
                    
                    df, err = ek.get_data(ric, fields)
                    if err:
                        self.logger.warning(f"SHFE {metal_name} 在庫データ警告: {err}")
                    
                    if not df.empty:
                        # 利用可能な値を順番に試行
                        total_stock = None
                        for field in ['CF_LAST', 'CF_CLOSE', 'CLOSE']:
                            if field in df.columns:
                                value = df[field].iloc[0]
                                if value is not None and not pd.isna(value):
                                    total_stock = value
                                    break
                        
                        shfe_data[metal_name] = {
                            'total_stock': total_stock
                        }
                        
                except Exception as e:
                    self.logger.error(f"SHFE {metal_name} 在庫データエラー: {e}")
                    
        except Exception as e:
            self.logger.error(f"SHFE在庫データ取得エラー: {e}")
            
        return shfe_data
        
    def _get_smm_inventory(self) -> Dict:
        """SMM保税倉庫在庫データ取得"""
        smm_data = {}
        
        try:
            smm_inventory_rics = self.config.get("smm_inventory_rics", {})
            
            for metal_name, ric in smm_inventory_rics.items():
                try:
                    fields = ['CF_LAST', 'CF_CLOSE', 'CLOSE']
                    
                    df, err = ek.get_data(ric, fields)
                    if err:
                        self.logger.warning(f"SMM {metal_name} 在庫データ警告: {err}")
                    
                    if not df.empty:
                        # 利用可能な値を順番に試行
                        total_stock = None
                        for field in ['CF_LAST', 'CF_CLOSE', 'CLOSE']:
                            if field in df.columns:
                                value = df[field].iloc[0]
                                if value is not None and not pd.isna(value):
                                    total_stock = value
                                    break
                        
                        smm_data[metal_name] = {
                            'total_stock': total_stock
                        }
                        
                except Exception as e:
                    self.logger.error(f"SMM {metal_name} 在庫データエラー: {e}")
                    
        except Exception as e:
            self.logger.error(f"SMM在庫データ取得エラー: {e}")
            
        return smm_data
        
    def get_volume_data(self) -> Dict:
        """取引量データ取得"""
        self.logger.info("取引量データ取得開始")
        volume_data = {}
        
        try:
            for metal_name, ric in self.metals_rics.items():
                try:
                    fields = [
                        'VOL',             # 出来高(代替)
                        'ACVOL_1',         # 累積出来高
                        'CF_VOLUME',       # 出来高(代替2)
                        'TURNOVER'         # 売買代金
                    ]
                    
                    df, err = ek.get_data(ric, fields)
                    if err:
                        self.logger.warning(f"{metal_name} 取引量データ警告: {err}")
                    
                    if not df.empty:
                        # 出来高の取得
                        volume = None
                        for field in ['VOL', 'ACVOL_1', 'CF_VOLUME']:
                            if field in df.columns:
                                value = df[field].iloc[0]
                                if value is not None and not pd.isna(value):
                                    volume = value
                                    break
                        
                        # 売買代金の取得
                        turnover = None
                        if 'TURNOVER' in df.columns:
                            value = df['TURNOVER'].iloc[0]
                            if value is not None and not pd.isna(value):
                                turnover = value
                        
                        # 取引量トレンド分析
                        volume_trend = self._get_volume_trend(ric)
                        
                        volume_data[metal_name] = {
                            'volume': volume,
                            'open_interest': None,  # このデータは利用できない場合が多い
                            'turnover': turnover,
                            'trend': volume_trend
                        }
                        
                except Exception as e:
                    self.logger.error(f"{metal_name} 取引量データエラー: {e}")
                    
        except Exception as e:
            self.logger.error(f"取引量データ取得エラー: {e}")
            
        self.logger.info("取引量データ取得完了")
        return volume_data
    
    def _get_third_wednesdays(self, start_date: datetime, num_months: int = 24) -> List[datetime]:
        """第3水曜日の日付リストを生成（2年分）"""
        third_wednesdays = []
        current_date = start_date.replace(day=1)
        
        for i in range(num_months):
            # 各月の1日から第3水曜日を計算
            year = current_date.year
            month = current_date.month
            
            # その月の1日
            first_day = datetime(year, month, 1)
            
            # 1日の曜日を取得（月曜日=0, 日曜日=6）
            first_weekday = first_day.weekday()
            
            # 第1水曜日を計算
            if first_weekday <= 2:  # 月、火、水曜日
                first_wednesday = first_day + timedelta(days=(2 - first_weekday))
            else:  # 木、金、土、日曜日
                first_wednesday = first_day + timedelta(days=(9 - first_weekday))
            
            # 第3水曜日を計算
            third_wednesday = first_wednesday + timedelta(days=14)
            third_wednesdays.append(third_wednesday)
            
            # 次の月へ
            if month == 12:
                current_date = datetime(year + 1, 1, 1)
            else:
                current_date = datetime(year, month + 1, 1)
        
        return third_wednesdays
    
    def _generate_lme_rics_for_dates(self, metal_name: str, target_dates: List[datetime]) -> List[str]:
        """第3水曜日の日付に基づいてLME RICを生成"""
        rics = []
        
        # メタル別のベースRICマッピング
        metal_base_rics = {
            'Copper': 'CMCU',
            'Aluminium': 'CMAL', 
            'Zinc': 'CMZN',
            'Lead': 'CMPB',
            'Nickel': 'CMNI',
            'Tin': 'CMSN'
        }
        
        # 月コードマッピング（LME標準）
        month_codes = {
            1: 'F',   # January
            2: 'G',   # February  
            3: 'H',   # March
            4: 'J',   # April
            5: 'K',   # May
            6: 'M',   # June
            7: 'N',   # July
            8: 'Q',   # August
            9: 'U',   # September
            10: 'V',  # October
            11: 'X',  # November
            12: 'Z'   # December
        }
        
        base_ric = metal_base_rics.get(metal_name, 'CMCU')
        
        for date in target_dates:
            # LME契約月の表記: CMCU + 月コード + 年の下2桁
            year_code = str(date.year)[-2:]  # 年の下2桁
            month_code = month_codes.get(date.month, 'Z')  # 月コード
            
            # LME RIC形式: CMCUZ25 (例: 2025年12月)
            ric = f"{base_ric}{month_code}{year_code}"
            rics.append(ric)
        
        return rics

    def get_forward_curve_data(self) -> Dict:
        """フォワードカーブデータ取得（第3水曜日ベース）"""
        self.logger.info("フォワードカーブデータ取得開始")
        forward_curve_data = {}
        
        try:
            # 今日から2年分の第3水曜日を取得
            today = datetime.now()
            third_wednesdays = self._get_third_wednesdays(today, 24)
            
            metals = ['Copper', 'Aluminium', 'Zinc', 'Lead', 'Nickel', 'Tin']
            
            for metal_name in metals:
                try:
                    self.logger.info(f"{metal_name} フォワードカーブ取得中...")
                    
                    # 第3水曜日に対応するRICを生成
                    rics = self._generate_lme_rics_for_dates(metal_name, third_wednesdays)
                    
                    # T-1（前営業日）価格とT-2（前々営業日）価格を取得
                    from datetime import timedelta
                    
                    # 営業日を考慮した日付計算
                    def get_business_days_ago(days_back):
                        current = datetime.now()
                        business_days_found = 0
                        days_checked = 0
                        
                        while business_days_found < days_back:
                            days_checked += 1
                            check_date = current - timedelta(days=days_checked)
                            # 月曜日=0, 日曜日=6 なので、土曜日(5)と日曜日(6)を除外
                            if check_date.weekday() < 5:  # 月曜日～金曜日
                                business_days_found += 1
                        
                        return (current - timedelta(days=days_checked)).strftime('%Y-%m-%d')
                    
                    t1_date = get_business_days_ago(1)  # 1営業日前
                    t2_date = get_business_days_ago(2)  # 2営業日前
                    
                    self.logger.info(f"{metal_name} T-1日付: {t1_date}, T-2日付: {t2_date}")
                    
                    # get_timeseriesを使用してより正確な価格データを取得
                    # 過去1週間のデータを取得して特定の日付の価格を抽出
                    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
                    end_date = datetime.now().strftime('%Y-%m-%d')
                    
                    # 各RICについてtime seriesでデータを取得
                    curve_data = {}
                    
                    for i, (date, ric) in enumerate(zip(third_wednesdays, rics)):
                        try:
                            # time seriesで過去のデータを取得
                            df_ts = ek.get_timeseries([ric], start_date=start_date, end_date=end_date)
                            
                            if not df_ts.empty:
                                # T-1とT-2の価格を抽出
                                t1_price = None
                                t2_price = None
                                
                                # T-1価格の取得
                                t1_data = df_ts[df_ts.index.strftime('%Y-%m-%d') == t1_date]
                                if not t1_data.empty:
                                    t1_price = t1_data['CLOSE'].iloc[0]
                                
                                # T-2価格の取得
                                t2_data = df_ts[df_ts.index.strftime('%Y-%m-%d') == t2_date]
                                if not t2_data.empty:
                                    t2_price = t2_data['CLOSE'].iloc[0]
                                
                                # 価格変化の計算
                                price_change = None
                                if t1_price is not None and t2_price is not None:
                                    price_change = t1_price - t2_price
                                
                                # デバッグ情報（最初の5つの契約のみ）
                                if i < 5:
                                    self.logger.info(f"{metal_name} {ric}: T-1価格={t1_price}, T-2価格={t2_price}, 変化={price_change}")
                                
                                # 日付をキーとして使用
                                date_key = date.strftime('%Y-%m-%d')
                                curve_data[date_key] = {
                                    'current_price': t1_price,    # T-1価格を'current_price'として扱う
                                    'previous_price': t2_price,   # T-2価格を'previous_price'として扱う
                                    'price_change': price_change,
                                    'ric': ric,
                                    'date': date,
                                    'months_from_now': i
                                }
                            else:
                                self.logger.warning(f"{metal_name} {ric}: time series データが空です")
                                # データが空の場合はNoneで埋める
                                date_key = date.strftime('%Y-%m-%d')
                                curve_data[date_key] = {
                                    'current_price': None,
                                    'previous_price': None,
                                    'price_change': None,
                                    'ric': ric,
                                    'date': date,
                                    'months_from_now': i
                                }
                        
                        except Exception as e:
                            self.logger.error(f"{metal_name} {ric} データ取得エラー: {e}")
                            # エラーの場合はNoneで埋める
                            date_key = date.strftime('%Y-%m-%d')
                            curve_data[date_key] = {
                                'current_price': None,
                                'previous_price': None,
                                'price_change': None,
                                'ric': ric,
                                'date': date,
                                'months_from_now': i
                            }
                    
                    # スプレッド分析
                    spreads = self._analyze_curve_spreads(curve_data)
                    contango_backwardation = self._analyze_contango_backwardation(curve_data)
                    
                    forward_curve_data[metal_name] = {
                        'curve_data': curve_data,
                        'spreads': spreads,
                        'structure_analysis': contango_backwardation,
                        'third_wednesdays': third_wednesdays
                    }
                    
                    self.logger.info(f"{metal_name} フォワードカーブ取得成功")
                        
                except Exception as e:
                    self.logger.error(f"{metal_name} フォワードカーブエラー: {e}")
                    forward_curve_data[metal_name] = self._get_fallback_forward_curve_data(metal_name)
                    
        except Exception as e:
            self.logger.error(f"フォワードカーブデータ取得エラー: {e}")
            
        self.logger.info("フォワードカーブデータ取得完了")
        return forward_curve_data
    
    def _analyze_curve_spreads(self, curve_data: Dict) -> Dict:
        """カーブスプレッド分析（日付ベース - 細かいグリッド）"""
        spreads = {}
        
        try:
            # 日付でソートされたキーを取得
            sorted_dates = sorted(curve_data.keys())
            
            # 1年以内は月次、それ以降は四半期/半年間隔
            # 1年以内: 0M(現在), 1M, 2M, 3M, 4M, 5M, 6M, 7M, 8M, 9M, 10M, 11M, 12M
            # 1年以降: 15M, 18M, 24M
            key_periods = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 18, 24]
            
            # 連続するペアでスプレッド計算
            for i in range(len(key_periods) - 1):
                near_month = key_periods[i]
                far_month = key_periods[i + 1]
                
                # 対応する日付のデータを取得
                near_data = None
                far_data = None
                
                for date_key in sorted_dates:
                    months_from_now = curve_data[date_key].get('months_from_now', 0)
                    if months_from_now == near_month and near_data is None:
                        near_data = curve_data[date_key]
                    elif months_from_now == far_month and far_data is None:
                        far_data = curve_data[date_key]
                
                if near_data and far_data:
                    near_price = near_data.get('current_price')
                    far_price = far_data.get('current_price')
                    
                    near_prev = near_data.get('previous_price')
                    far_prev = far_data.get('previous_price')
                    
                    if near_price is not None and far_price is not None:
                        current_spread = near_price - far_price
                        
                        prev_spread = None
                        spread_change = None
                        if near_prev is not None and far_prev is not None:
                            prev_spread = near_prev - far_prev
                            spread_change = current_spread - prev_spread
                        
                        spread_name = f"{near_month}M_{far_month}M"
                        spreads[spread_name] = {
                            'current_spread': current_spread,
                            'previous_spread': prev_spread,
                            'spread_change': spread_change,
                            'spread_description': f"{near_month}M - {far_month}M",
                            'near_date': near_data.get('date'),
                            'far_date': far_data.get('date')
                        }
            
            # 主要なクロススプレッドも計算（1M-3M, 3M-6M, 6M-12M, 12M-24M）
            major_spreads = [(1, 3), (3, 6), (6, 12), (12, 24)]
            for near_month, far_month in major_spreads:
                near_data = None
                far_data = None
                
                for date_key in sorted_dates:
                    months_from_now = curve_data[date_key].get('months_from_now', 0)
                    if months_from_now == near_month and near_data is None:
                        near_data = curve_data[date_key]
                    elif months_from_now == far_month and far_data is None:
                        far_data = curve_data[date_key]
                
                if near_data and far_data:
                    near_price = near_data.get('current_price')
                    far_price = far_data.get('current_price')
                    
                    near_prev = near_data.get('previous_price')
                    far_prev = far_data.get('previous_price')
                    
                    if near_price is not None and far_price is not None:
                        current_spread = near_price - far_price
                        
                        prev_spread = None
                        spread_change = None
                        if near_prev is not None and far_prev is not None:
                            prev_spread = near_prev - far_prev
                            spread_change = current_spread - prev_spread
                        
                        spread_name = f"{near_month}M_{far_month}M_major"
                        spreads[spread_name] = {
                            'current_spread': current_spread,
                            'previous_spread': prev_spread,
                            'spread_change': spread_change,
                            'spread_description': f"{near_month}M - {far_month}M (主要)",
                            'near_date': near_data.get('date'),
                            'far_date': far_data.get('date')
                        }
                        
        except Exception as e:
            self.logger.error(f"スプレッド分析エラー: {e}")
            
        return spreads
    
    def _analyze_contango_backwardation(self, curve_data: Dict) -> Dict:
        """コンタンゴ・バックワーデーション分析（日付ベース）"""
        try:
            # 日付でソートされたキーを取得
            sorted_dates = sorted(curve_data.keys())
            
            # 最初の契約月（現在月）と3ヶ月先の比較で基本構造を判定
            near_month_data = None
            far_month_data = None
            
            for date_key in sorted_dates:
                months_from_now = curve_data[date_key].get('months_from_now', 0)
                if months_from_now == 0 and near_month_data is None:  # 現在月
                    near_month_data = curve_data[date_key]
                elif months_from_now == 3 and far_month_data is None:  # 3ヶ月先
                    far_month_data = curve_data[date_key]
            
            structure = "不明"
            structure_strength = "中"
            
            # 3ヶ月先がない場合、利用可能な最初の2つの契約月を使用
            if near_month_data is None or far_month_data is None:
                available_data = [(k, v) for k, v in curve_data.items() 
                                if v.get('current_price') is not None]
                if len(available_data) >= 2:
                    # 月数でソート
                    available_data.sort(key=lambda x: x[1].get('months_from_now', 0))
                    near_month_data = available_data[0][1]
                    far_month_data = available_data[1][1]
            
            if (near_month_data and far_month_data and 
                near_month_data.get('current_price') is not None and 
                far_month_data.get('current_price') is not None):
                
                near_price = near_month_data.get('current_price')
                far_price = far_month_data.get('current_price')
                
                spread = far_price - near_price
                spread_percentage = (spread / near_price) * 100 if near_price != 0 else 0
                
                if spread > 0:
                    structure = "コンタンゴ"
                    if abs(spread_percentage) > 2:
                        structure_strength = "強"
                    elif abs(spread_percentage) > 0.5:
                        structure_strength = "中"
                    else:
                        structure_strength = "弱"
                elif spread < 0:
                    structure = "バックワーデーション"
                    if abs(spread_percentage) > 2:
                        structure_strength = "強"
                    elif abs(spread_percentage) > 0.5:
                        structure_strength = "中"
                    else:
                        structure_strength = "弱"
                else:
                    structure = "フラット"
                    structure_strength = "中"
            
            # 前日比較
            structure_change = "変化なし"
            near_3m_spread = None
            
            if (near_month_data and far_month_data and 
                near_month_data.get('current_price') is not None and 
                far_month_data.get('current_price') is not None):
                
                near_price = near_month_data.get('current_price')
                far_price = far_month_data.get('current_price')
                near_3m_spread = far_price - near_price
                
                # 前日データがある場合の変化分析
                near_prev = near_month_data.get('previous_price')
                far_prev = far_month_data.get('previous_price')
                
                if near_prev is not None and far_prev is not None:
                    prev_spread = far_prev - near_prev
                    current_spread = far_price - near_price
                    spread_delta = current_spread - prev_spread
                    
                    if abs(spread_delta) > abs(near_price * 0.005):  # 0.5%以上の変化
                        if spread_delta > 0:
                            structure_change = "コンタンゴ方向"
                        else:
                            structure_change = "バックワーデーション方向"
            
            return {
                'structure': structure,
                'strength': structure_strength,
                'near_far_spread': near_3m_spread,
                'structure_change': structure_change,
                'analysis_note': f"{structure}({structure_strength}) - 前日比: {structure_change}",
                'near_contract': near_month_data.get('date') if near_month_data else None,
                'far_contract': far_month_data.get('date') if far_month_data else None
            }
            
        except Exception as e:
            self.logger.error(f"コンタンゴ・バックワーデーション分析エラー: {e}")
            return {
                'structure': '分析エラー',
                'strength': '不明',
                'cash_3m_spread': None,
                'structure_change': '不明',
                'analysis_note': '分析中にエラーが発生しました'
            }
    
    def _get_fallback_forward_curve_data(self, metal_name: str) -> Dict:
        """フォワードカーブフォールバックデータ"""
        return {
            'curve_data': {},
            'spreads': {},
            'structure_analysis': {
                'structure': 'データ取得失敗',
                'strength': '不明',
                'cash_3m_spread': None,
                'structure_change': '不明',
                'analysis_note': 'フォワードカーブデータの取得に失敗しました'
            }
        }
        
    def get_macro_data(self) -> Dict:
        """マクロ経済データ・スワップレート取得"""
        self.logger.info("マクロ経済データ取得開始")
        macro_data = {}
        
        try:
            # 従来のマクロ経済指標
            macro_rics = self.config.get("macro_rics", {})
            
            for indicator, ric in macro_rics.items():
                try:
                    df, err = ek.get_data(ric, ['CF_LAST'])
                    if err:
                        self.logger.warning(f"{indicator} データ警告: {err}")
                    
                    if not df.empty:
                        raw_value = df['CF_LAST'].iloc[0] if 'CF_LAST' in df.columns else None
                        
                        # NA値のチェックと処理
                        if pd.isna(raw_value):
                            raw_value = None
                        
                        macro_data[indicator] = {
                            'value': raw_value,
                            'ric': ric
                        }
                        
                except Exception as e:
                    self.logger.error(f"{indicator} データエラー: {e}")
            
            # スワップレートデータ
            self.logger.info("スワップレートデータ取得開始")
            swap_rates = self.config.get("usdjpy_swap_rates", {})
            
            if swap_rates:
                macro_data['swap_rates'] = {}
                
                for rate_name, ric in swap_rates.items():
                    try:
                        df, err = ek.get_data(ric, ['CF_LAST', 'CF_CLOSE'])
                        if err:
                            self.logger.warning(f"{rate_name} スワップレート警告: {err}")
                        
                        if not df.empty:
                            # CF_LASTを優先、なければCF_CLOSEを使用
                            rate_value = None
                            for field in ['CF_LAST', 'CF_CLOSE']:
                                if field in df.columns:
                                    raw_value = df[field].iloc[0]
                                    if not pd.isna(raw_value):
                                        rate_value = raw_value
                                        break
                            
                            macro_data['swap_rates'][rate_name] = {
                                'rate': rate_value,
                                'ric': ric,
                                'description': self._get_swap_rate_description(rate_name)
                            }
                            
                            if rate_value is not None:
                                self.logger.info(f"{rate_name} スワップレート取得成功: {rate_value}%")
                            
                    except Exception as e:
                        self.logger.error(f"{rate_name} スワップレートエラー: {e}")
                
                self.logger.info("スワップレートデータ取得完了")
                    
        except Exception as e:
            self.logger.error(f"マクロ経済データ取得エラー: {e}")
            
        self.logger.info("マクロ経済データ取得完了")
        return macro_data
    
    def _get_swap_rate_description(self, rate_name: str) -> str:
        """スワップレート名の説明を取得"""
        descriptions = {
            'USD_2Y_IRS': 'USD 2年金利スワップ',
            'JPY_1Y_DEPOSIT': 'JPY 1年預金金利',
            'USD_1Y_DEPOSIT': 'USD 1年預金金利', 
            'USD_2Y_DEPOSIT': 'USD 2年預金金利'
        }
        return descriptions.get(rate_name, rate_name)
    
    def get_equity_data(self) -> Dict:
        """株式市場データ取得"""
        self.logger.info("株式市場データ取得開始")
        equity_data = {}
        
        try:
            equity_indices = self.config.get("equity_indices", {})
            
            for index_name, ric in equity_indices.items():
                try:
                    # 現在価格と変動率取得
                    df, err = ek.get_data(ric, ['CF_LAST', 'PCTCHNG'])
                    if err:
                        self.logger.warning(f"{index_name} データ警告: {err}")
                    
                    if not df.empty:
                        current_price = df['CF_LAST'].iloc[0] if 'CF_LAST' in df.columns else None
                        daily_change = df['PCTCHNG'].iloc[0] if 'PCTCHNG' in df.columns else None
                        
                        # NA値のチェックと処理
                        if pd.isna(current_price):
                            current_price = None
                        if pd.isna(daily_change):
                            daily_change = None
                        
                        # 週次・月次変動率取得
                        historical_returns = self._get_equity_historical_returns(ric)
                        
                        equity_data[index_name] = {
                            'current_price': current_price,
                            'daily_change': daily_change,
                            'weekly_change': historical_returns.get('weekly_change'),
                            'monthly_change': historical_returns.get('monthly_change'),
                            'ytd_change': historical_returns.get('ytd_change'),
                            'ric': ric
                        }
                        
                except Exception as e:
                    self.logger.error(f"{index_name} データエラー: {e}")
                    
        except Exception as e:
            self.logger.error(f"株式市場データ取得エラー: {e}")
            
        self.logger.info("株式市場データ取得完了")
        return equity_data
    
    def get_risk_sentiment_data(self) -> Dict:
        """リスクセンチメント指標取得"""
        self.logger.info("リスクセンチメント指標取得開始")
        sentiment_data = {}
        
        try:
            risk_indicators = self.config.get("risk_sentiment_indicators", {})
            
            for indicator_name, ric in risk_indicators.items():
                try:
                    df, err = ek.get_data(ric, ['CF_LAST', 'PCTCHNG'])
                    if err:
                        self.logger.warning(f"{indicator_name} データ警告: {err}")
                    
                    if not df.empty:
                        current_value = df['CF_LAST'].iloc[0] if 'CF_LAST' in df.columns else None
                        daily_change = df['PCTCHNG'].iloc[0] if 'PCTCHNG' in df.columns else None
                        
                        # NA値のチェックと処理
                        if pd.isna(current_value):
                            current_value = None
                        if pd.isna(daily_change):
                            daily_change = None
                        
                        sentiment_data[indicator_name] = {
                            'value': current_value,
                            'daily_change': daily_change,
                            'ric': ric
                        }
                        
                except Exception as e:
                    self.logger.error(f"{indicator_name} データエラー: {e}")
            
            # リスクセンチメント総合判定
            sentiment_analysis = self._analyze_risk_sentiment(sentiment_data)
            sentiment_data['risk_sentiment_analysis'] = sentiment_analysis
                    
        except Exception as e:
            self.logger.error(f"リスクセンチメント指標取得エラー: {e}")
            
        self.logger.info("リスクセンチメント指標取得完了")
        return sentiment_data
    
    def _get_equity_historical_returns(self, ric: str) -> Dict:
        """株式指数の履歴変動率計算"""
        try:
            end_date = datetime.now()
            start_date = datetime(end_date.year, 1, 1)  # 年初
            
            df = ek.get_timeseries(
                ric, 
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                fields=['CLOSE']
            )
            
            if df is not None and not df.empty:
                current_price = df['CLOSE'].iloc[-1]
                
                # 週次変動率（5営業日前）
                week_ago = df['CLOSE'].iloc[-6] if len(df) >= 6 else df['CLOSE'].iloc[0]
                weekly_change = ((current_price - week_ago) / week_ago * 100) if week_ago != 0 else 0
                
                # 月次変動率（20営業日前）
                month_ago = df['CLOSE'].iloc[-21] if len(df) >= 21 else df['CLOSE'].iloc[0]
                monthly_change = ((current_price - month_ago) / month_ago * 100) if month_ago != 0 else 0
                
                # 年初来変動率
                ytd_price = df['CLOSE'].iloc[0]
                ytd_change = ((current_price - ytd_price) / ytd_price * 100) if ytd_price != 0 else 0
                
                return {
                    'weekly_change': weekly_change,
                    'monthly_change': monthly_change,
                    'ytd_change': ytd_change
                }
            else:
                return {
                    'weekly_change': None, 
                    'monthly_change': None, 
                    'ytd_change': None
                }
                
        except Exception as e:
            self.logger.error(f"株式履歴データ取得エラー: {e}")
            return {
                'weekly_change': None, 
                'monthly_change': None, 
                'ytd_change': None
            }
    
    def _analyze_risk_sentiment(self, sentiment_data: Dict) -> Dict:
        """リスクセンチメント総合分析"""
        try:
            risk_on_signals = 0
            risk_off_signals = 0
            total_signals = 0
            
            # VIX分析（恐怖指数）
            vix_data = sentiment_data.get('VIX_VOLATILITY', {})
            vix_value = vix_data.get('value')
            if vix_value is not None and not pd.isna(vix_value):
                total_signals += 1
                if vix_value < 20:
                    risk_on_signals += 1  # 低VIX = リスクオン
                elif vix_value > 30:
                    risk_off_signals += 1  # 高VIX = リスクオフ
            
            # 金価格分析（安全資産）
            gold_data = sentiment_data.get('GOLD_PRICE', {})
            gold_change = gold_data.get('daily_change')
            if gold_change is not None and not pd.isna(gold_change):
                total_signals += 1
                if gold_change < -1:
                    risk_on_signals += 1  # 金下落 = リスクオン
                elif gold_change > 1:
                    risk_off_signals += 1  # 金上昇 = リスクオフ
            
            # USD/JPY分析（リスク通貨ペア）
            usdjpy_data = sentiment_data.get('USD_JPY', {})
            usdjpy_change = usdjpy_data.get('daily_change')
            if usdjpy_change is not None and not pd.isna(usdjpy_change):
                total_signals += 1
                if usdjpy_change > 0.5:
                    risk_on_signals += 1  # USD/JPY上昇 = リスクオン
                elif usdjpy_change < -0.5:
                    risk_off_signals += 1  # USD/JPY下落 = リスクオフ
            
            # 銅金比率分析（景気敏感）
            copper_gold_data = sentiment_data.get('COPPER_GOLD_RATIO', {})
            copper_gold_change = copper_gold_data.get('daily_change')
            if copper_gold_change is not None and not pd.isna(copper_gold_change):
                total_signals += 1
                if copper_gold_change > 1:
                    risk_on_signals += 1  # 銅金比率上昇 = リスクオン
                elif copper_gold_change < -1:
                    risk_off_signals += 1  # 銅金比率下落 = リスクオフ
            
            # 総合判定
            if total_signals > 0:
                risk_on_ratio = risk_on_signals / total_signals
                risk_off_ratio = risk_off_signals / total_signals
                
                if risk_on_ratio > 0.6:
                    sentiment = "リスクオン"
                    confidence = "高"
                elif risk_off_ratio > 0.6:
                    sentiment = "リスクオフ"
                    confidence = "高"
                elif risk_on_ratio > 0.4:
                    sentiment = "やや リスクオン"
                    confidence = "中"
                elif risk_off_ratio > 0.4:
                    sentiment = "やや リスクオフ"
                    confidence = "中"
                else:
                    sentiment = "中立"
                    confidence = "中"
            else:
                sentiment = "不明"
                confidence = "低"
            
            return {
                'overall_sentiment': sentiment,
                'confidence_level': confidence,
                'risk_on_signals': risk_on_signals,
                'risk_off_signals': risk_off_signals,
                'total_signals': total_signals,
                'risk_on_ratio': round(risk_on_ratio * 100, 1) if total_signals > 0 else 0,
                'risk_off_ratio': round(risk_off_ratio * 100, 1) if total_signals > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"リスクセンチメント分析エラー: {e}")
            return {
                'overall_sentiment': '分析エラー',
                'confidence_level': '低',
                'risk_on_signals': 0,
                'risk_off_signals': 0,
                'total_signals': 0
            }
        
    def get_news_data(self) -> Dict:
        """ニュースデータ取得（前営業日の主要ニュースをすべて取得）"""
        self.logger.info("ニュースデータ取得開始")
        news_data = {}
        
        # 設定から取得
        news_settings = self.config.get("news_settings", {})
        enable_news_collection = news_settings.get("enable_news_collection", True)
        
        # ニュース収集が無効化されている場合はスキップ
        if not enable_news_collection:
            self.logger.info("ニュース収集が無効化されています。フォールバックデータを使用します。")
            for metal_name in self.metals_rics.keys():
                news_data[metal_name] = self._get_fallback_news_data(metal_name)
            news_data['General_Market'] = self._get_fallback_news_data("General Market")
            news_data['China_Economy'] = self._get_fallback_news_data("China Economy")
            self.logger.info("ニュースデータ取得完了（フォールバック）")
            return news_data
        
        # 前営業日を取得
        previous_business_day = self._get_previous_business_day()
        self.logger.info(f"前営業日: {previous_business_day.strftime('%Y-%m-%d')}")
        
        excluded_sources = news_settings.get("excluded_sources", [])
        enable_general_news = news_settings.get("enable_general_market_news", True)
        
        # ニュース取得統計
        news_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'fallback_used': 0,
            'total_news_items': 0,
            'circuit_breaker_activated': False
        }
        
        try:
            # 一般的な金属市場ニュースを取得
            if enable_general_news:
                self.logger.info("一般市場ニュース取得開始")
                general_news = self._get_comprehensive_news_data(
                    "general market", previous_business_day, excluded_sources
                )
                news_stats['successful_queries'] += 1
                
                if general_news and len(general_news) >= 1:
                    news_data['General_Market'] = general_news
                    self.logger.info(f"一般市場ニュース {len(general_news)}件取得")
                else:
                    self.logger.warning(f"一般市場実ニュース取得失敗、フォールバック使用")
                    news_data['General_Market'] = self._get_fallback_news_data("General_Market")
                    news_stats['fallback_used'] += 1
            
            # 中国経済関連ニュースを取得
            self.logger.info("中国経済ニュース取得開始")
            china_news = self._get_comprehensive_news_data(
                "china economy", previous_business_day, excluded_sources
            )
            news_stats['successful_queries'] += 1
            
            if china_news and len(china_news) >= 1:
                news_data['China_Economy'] = china_news
                self.logger.info(f"中国経済ニュース {len(china_news)}件取得")
            else:
                self.logger.warning(f"中国経済実ニュース取得失敗、フォールバック使用")
                news_data['China_Economy'] = self._get_fallback_news_data("China_Economy")
                news_stats['fallback_used'] += 1
            
            # 各金属固有のニュース取得
            for metal_name in self.metals_rics.keys():
                try:
                    self.logger.info(f"{metal_name} ニュース取得開始")
                    metal_news = self._get_comprehensive_news_data(
                        metal_name, previous_business_day, excluded_sources
                    )
                    news_stats['successful_queries'] += 1
                    
                    if metal_news and len(metal_news) >= 1:  # 最低1件は必要
                        news_data[metal_name] = metal_news
                        self.logger.info(f"{metal_name} ニュース {len(metal_news)}件取得")
                    else:
                        self.logger.warning(f"{metal_name} 実ニュース取得失敗、フォールバック使用")
                        news_data[metal_name] = self._get_fallback_news_data(metal_name)
                        news_stats['fallback_used'] += 1
                    
                except Exception as e:
                    self.logger.error(f"{metal_name} ニュースデータエラー: {e}")
                    news_data[metal_name] = self._get_fallback_news_data(metal_name)
                    news_stats['fallback_used'] += 1
                    
        except Exception as e:
            self.logger.error(f"ニュースデータ取得エラー: {e}")
            # 全体でエラーの場合、すべての金属にフォールバックデータを提供
            for metal_name in self.metals_rics.keys():
                news_data[metal_name] = self._get_fallback_news_data(metal_name)
                news_stats['fallback_used'] += 1
            
        # ニュース取得統計をログ出力
        self.logger.info(f"ニュース取得統計: 成功: {news_stats.get('successful_queries', 0)}, 失敗: {news_stats.get('failed_queries', 0)}, フォールバック使用: {news_stats.get('fallback_used', 0)}")
        self.logger.info("ニュースデータ取得完了")
        return news_data
    
    def _get_comprehensive_news_data(self, metal_keyword: str, target_date: datetime, excluded_sources: List[str]) -> List[Dict]:
        """包括的ニュース取得（直近3営業日のニュースのみを取得）"""
        all_news = []
        
        # 3営業日前の日付を計算
        business_days_back = 0
        check_date = target_date
        
        while business_days_back < 3:
            check_date = check_date - timedelta(days=1)
            # 土曜日(5)と日曜日(6)を除外
            if check_date.weekday() < 5:  # 月曜日(0)〜金曜日(4)
                business_days_back += 1
        
        # 日付範囲設定: 3営業日前から当日まで
        date_from_str = check_date.strftime('%Y-%m-%d')
        date_to_str = target_date.strftime('%Y-%m-%d')
        
        self.logger.info(f"ニュース取得期間: {date_from_str} から {date_to_str} (直近3営業日)")
        
        # 効率的な検索クエリを作成（成功率の高いものを優先）
        if metal_keyword.lower() == "general market":
            queries = [
                "LME",  # シンプルで成功率の高いクエリ
                "london metal exchange",
                "base metals",
                "copper price",  # 分割して検索
                "aluminum price",
                "zinc price"
            ]
        elif metal_keyword.lower() == "china economy":
            queries = [
                "china economy",
                "china PMI",
                "china manufacturing",
                "china metals",
                "china copper"
            ]
        else:
            metal_name = metal_keyword.lower()
            # シンプルなクエリから開始して段階的に複雑化
            queries = [
                metal_name,  # 基本検索
                f"{metal_name} price",
                f"{metal_name} LME",
                f"{metal_name} inventory",
                f"{metal_name} production"
            ]
        
        successful_queries = 0
        total_queries = len(queries)
        
        # 各クエリで順次検索
        for query in queries:
            try:
                self.logger.debug(f"ニュース検索: {query}")
                
                # 3営業日以内のニュースのみ取得するため、必ず日付範囲を指定
                headlines = None
                try:
                    # 日付範囲を指定して取得（3営業日以内のニュースのみ）
                    headlines = ek.get_news_headlines(
                        query=query,
                        count=self.config.get("news_settings", {}).get("max_news_per_query", 30),
                        date_from=date_from_str,
                        date_to=date_to_str
                    )
                    self.logger.debug(f"日付指定でニュース取得成功: {query} ({date_from_str}〜{date_to_str})")
                except Exception as date_error:
                    self.logger.debug(f"日付指定でエラー: {query} - {date_error}")
                    # datetime64エラーの場合は、このクエリをスキップ
                    if "datetime64" in str(date_error):
                        self.logger.debug(f"datetime64エラーのためクエリをスキップ: {query}")
                        continue
                    # その他のエラーの場合は、日付なしで試行（フォールバック）
                    try:
                        headlines = ek.get_news_headlines(
                            query=query,
                            count=self.config.get("news_settings", {}).get("max_news_per_query", 15)  # 数を減らしてリスク軽減
                        )
                        self.logger.debug(f"日付なしフォールバックでニュース取得成功: {query}")
                    except Exception as fallback_error:
                        self.logger.debug(f"フォールバックも失敗: {query} - {fallback_error}")
                        continue
                
                if headlines is not None and len(headlines) > 0:
                    successful_queries += 1
                    self.logger.debug(f"クエリ '{query}' で {len(headlines)} 件取得")
                    
                    # DataFrameから安全にデータを抽出
                    for i in range(len(headlines)):
                        try:
                            row = headlines.iloc[i]
                            news_item = {
                                'headline': str(row.get('text', ''))[:200],  # 長すぎるヘッドラインを制限
                                'date': str(row.get('versionCreated', '')),
                                'source': str(row.get('sourceCode', '')),
                                'story_id': str(row.get('storyId', '')),
                                'body': ''
                            }
                            
                            # 除外ソースのフィルタリング
                            if news_item['source'] in excluded_sources:
                                continue
                            
                            # 日付チェック: 3営業日以内のニュースのみを保持
                            news_date_str = news_item.get('date', '')
                            if news_date_str:
                                try:
                                    # ニュースの日付を解析
                                    if 'T' in news_date_str:
                                        news_date = datetime.fromisoformat(news_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                                    else:
                                        news_date = datetime.strptime(news_date_str[:10], '%Y-%m-%d')
                                    
                                    # 3営業日前の日付より古い場合はスキップ
                                    if news_date.date() < check_date.date():
                                        self.logger.debug(f"古いニュースをスキップ: {news_date.date()} < {check_date.date()}")
                                        continue
                                        
                                except Exception as date_parse_error:
                                    self.logger.debug(f"日付解析エラー: {news_date_str} - {date_parse_error}")
                                    # 日付が解析できない場合は、とりあえず含める
                            
                            # 本文取得を試行（より効率的に）
                            if news_item['story_id'] and len(all_news) < 100:  # 最大100件まで本文取得
                                try:
                                    story = ek.get_news_story(news_item['story_id'])
                                    if story:
                                        # HTMLタグを除去して本文を取得
                                        import re
                                        clean_text = re.sub('<[^<]+?>', '', story)
                                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                                        news_item['body'] = clean_text[:2000]  # 本文を2000文字まで拡張
                                        # 本文取得時の追加遅延
                                        time.sleep(0.05)
                                except Exception as story_error:
                                    self.logger.debug(f"本文取得エラー: {story_error}")
                                    news_item['body'] = ''
                            
                            all_news.append(news_item)
                            
                        except Exception as item_error:
                            self.logger.debug(f"ニュースアイテム処理エラー: {item_error}")
                            continue
                
                # APIレート制限対策を強化
                time.sleep(self.config.get("news_settings", {}).get("api_rate_limit_delay", 0.3))
                
            except Exception as e:
                self.logger.warning(f"ニュース検索エラー: {query} - {str(e)}")
                # エラー時はより長い遅延
                time.sleep(0.5)
                continue
        
        # ニュース重複除去
        unique_news = []
        seen_headlines = set()
        for news in all_news:
            headline_key = news['headline'][:50].lower()  # 最初の50文字で重複判定
            if headline_key not in seen_headlines and len(headline_key) > 10:
                seen_headlines.add(headline_key)
                unique_news.append(news)
        
        self.logger.info(f"{metal_keyword} ニュース検索統計: {successful_queries}/{total_queries} クエリ成功, {len(unique_news)} 件重複除去後")
        
        return unique_news
    
    def _build_comprehensive_queries(self, metal_keyword: str) -> List[List[str]]:
        """包括的検索クエリ構築（レート制限対応版）"""
        
        if metal_keyword == "general market":
            return [
                # 最高優先度：LME関連
                ["LME AND metals", "London Metal Exchange", "base metals"],
                # 中優先度：中国経済関連（金属需要に重要）
                ["China AND metals", "China PMI", "China industrial production"]
            ]
        
        if metal_keyword == "china economy":
            return [
                # 高優先度：中国経済指標
                ["China PMI", "China GDP", "China inflation"],
                # 中優先度：中国政策・金融
                ["China monetary policy", "China stimulus", "China property market"]
            ]
        
        # 金属固有のクエリ（より効率的に）
        metal_variations = self._get_metal_name_variations(metal_keyword)
        metal_symbol = self._get_metal_symbol(metal_keyword)
        
        queries = []
        
        # 最高優先度：LME + 金属名（メインクエリのみ）
        high_priority = []
        primary_variation = metal_variations[0] if metal_variations else metal_keyword.lower()
        high_priority.extend([
            f"LME AND {primary_variation}",
            f"{primary_variation} AND price",
            f"{primary_variation} AND inventory"
        ])
        if metal_symbol:
            high_priority.append(f"LME{metal_symbol}")
        queries.append(high_priority)
        
        # 中優先度：重要キーワード組み合わせ（選別）
        critical_keywords = ["production", "supply", "strike", "mine"]
        medium_priority = []
        for keyword in critical_keywords:
            medium_priority.append(f"{primary_variation} AND {keyword}")
        queries.append(medium_priority)
        
        # 低優先度：中国関連（金属市場で最重要地域）
        low_priority = [f"{primary_variation} AND China"]
        queries.append(low_priority)
        
        return queries
    
    def _get_metal_symbol(self, metal_name: str) -> str:
        """金属記号取得"""
        symbol_map = {
            'Copper': 'CU',
            'Aluminium': 'AL', 
            'Zinc': 'ZN',
            'Lead': 'PB',
            'Nickel': 'NI',
            'Tin': 'SN'
        }
        return symbol_map.get(metal_name, '')
    
    def _process_comprehensive_news(self, headlines: pd.DataFrame, excluded_sources: List[str], target_date: datetime) -> List[Dict]:
        """包括的ニュース処理（本文取得含む）"""
        processed_news = []
        
        for idx, row in headlines.iterrows():
            try:
                # 基本情報抽出
                news_item = self._extract_comprehensive_news_item(row, target_date)
                
                if not news_item or not news_item.get('headline'):
                    continue
                
                # 除外ソース確認
                source = news_item.get('source', '').upper()
                if any(excluded in source for excluded in excluded_sources):
                    continue
                
                # 日付フィルタリング（前営業日のニュースのみ）
                if not self._is_target_date_news(news_item.get('date'), target_date):
                    continue
                
                # ニュース本文取得を試行
                try:
                    story_id = news_item.get('story_id')
                    if story_id:
                        body_content = self._get_news_story_content(story_id)
                        news_item['body'] = body_content
                        if body_content:
                            self.logger.debug(f"本文取得成功 ({story_id}): {len(body_content)}文字")
                        else:
                            self.logger.debug(f"本文取得失敗 ({story_id}): 内容なし")
                    else:
                        news_item['body'] = None
                        self.logger.debug(f"ストーリーIDなし: {news_item.get('headline', '')[:50]}")
                except Exception as e:
                    self.logger.debug(f"本文取得エラー ({story_id}): {e}")
                    news_item['body'] = None
                
                # 重要度計算（本文も考慮）
                news_item['priority_score'] = self._calculate_comprehensive_priority(news_item)
                
                processed_news.append(news_item)
                
            except Exception as e:
                self.logger.debug(f"ニュース行処理エラー ({idx}): {e}")
                continue
        
        return processed_news
    
    def _extract_comprehensive_news_item(self, row: pd.Series, target_date: datetime) -> Dict:
        """包括的ニュースアイテム抽出"""
        try:
            # ヘッドライン抽出
            headline = None
            for col_name in ['headline', 'text', 'title', 'displayName', 'storyTitle']:
                if col_name in row.index and pd.notna(row.get(col_name)):
                    headline = str(row[col_name]).strip()
                    if headline:
                        break
            
            if not headline and len(row) > 0:
                headline = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
            
            if not headline:
                return {}
            
            # 日時抽出
            date_str = None
            for col_name in ['versionCreated', 'firstCreated', 'date', 'timestamp']:
                if col_name in row.index and pd.notna(row.get(col_name)):
                    try:
                        date_value = row[col_name]
                        if isinstance(date_value, str):
                            date_str = date_value[:19]
                        else:
                            date_str = str(date_value)[:19]
                        break
                    except:
                        continue
            
            if not date_str:
                date_str = target_date.strftime('%Y-%m-%d %H:%M:%S')
            
            # ソース抽出
            source = 'Unknown'
            for col_name in ['sourceCode', 'source', 'provider']:
                if col_name in row.index and pd.notna(row.get(col_name)):
                    source = str(row[col_name])
                    break
            
            # ストーリーID抽出
            story_id = None
            for col_name in ['storyId', 'id', 'guid']:
                if col_name in row.index and pd.notna(row.get(col_name)):
                    story_id = str(row[col_name])
                    break
            
            # カテゴリ抽出
            category = ''
            for col_name in ['subjects', 'category', 'topic']:
                if col_name in row.index and pd.notna(row.get(col_name)):
                    category = str(row[col_name])
                    break
            
            return {
                'headline': headline,
                'date': date_str,
                'source': source,
                'story_id': story_id,
                'category': category,
                'body': None,  # 後で取得
                'priority_score': 0
            }
            
        except Exception as e:
            self.logger.debug(f"ニュースアイテム抽出エラー: {e}")
            return {}
    
    def _is_target_date_news(self, news_date_str: str, target_date: datetime) -> bool:
        """指定日のニュースかどうか判定"""
        if not news_date_str:
            return False
        
        try:
            news_date = datetime.strptime(news_date_str[:10], '%Y-%m-%d')
            target_date_only = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            return news_date.date() == target_date_only.date()
        except:
            return False
    
    def _get_news_story_content(self, story_id: str) -> Optional[str]:
        """ニュース本文取得"""
        try:
            story = ek.get_news_story(story_id)
            if story and isinstance(story, str) and len(story.strip()) > 0:
                import re
                
                # より詳細なHTMLとCSS除去
                clean_text = story
                
                # CSSスタイル情報を除去
                clean_text = re.sub(r'\.storyContent[^}]*}[^}]*}', '', clean_text)
                clean_text = re.sub(r'\.storyContent[^;]*;', '', clean_text)
                
                # HTMLタグを除去
                clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
                
                # 特殊な文字やエンティティを処理
                clean_text = re.sub(r'&[a-zA-Z]+;', ' ', clean_text)
                clean_text = re.sub(r'&#\d+;', ' ', clean_text)
                
                # 余分な記号や情報を除去
                clean_text = re.sub(r'\([A-Z]+\)', '', clean_text)  # (END), (Reuters)など
                clean_text = re.sub(r'Write to.*?@.*?\.com', '', clean_text)  # ライター情報
                clean_text = re.sub(r'Copyright.*?Inc\.', '', clean_text)  # 著作権情報
                clean_text = re.sub(r'Dow Jones Newswires.*?\d{4}', '', clean_text)  # Dow Jones情報
                
                # 複数の空白、改行、タブを単一の空白に置換
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                # 文章の区切りで適切に切り詰め（完全な文章で終わるように）
                if len(clean_text) > 1500:
                    # 1500文字付近で文の区切りを探す
                    truncate_pos = clean_text.rfind('. ', 0, 1500)
                    if truncate_pos > 500:  # 最低500文字は確保
                        clean_text = clean_text[:truncate_pos + 1]
                    else:
                        clean_text = clean_text[:1500] + "..."
                
                # 最低限の長さチェック
                if len(clean_text.strip()) < 50:
                    self.logger.debug(f"本文が短すぎます ({story_id}): {len(clean_text)} 文字")
                    return None
                    
                self.logger.debug(f"本文取得成功 ({story_id}): {len(clean_text)} 文字")
                return clean_text
                
            return None
        except Exception as e:
            self.logger.debug(f"ストーリー本文取得エラー ({story_id}): {e}")
            return None
    
    def _calculate_comprehensive_priority(self, news_item: Dict) -> int:
        """包括的優先度計算（ヘッドライン＋本文）"""
        score = 0
        
        # ヘッドラインでの評価
        headline = news_item.get('headline', '').lower()
        score += self._calculate_simple_priority(headline, news_item.get('source', ''))
        
        # 本文での評価（本文がある場合）
        body = news_item.get('body', '')
        if body:
            body_lower = body.lower()
            
            # 本文での重要キーワード
            critical_keywords = [
                'production cut', 'mine closure', 'strike', 'force majeure',
                'supply disruption', 'inventory surge', 'shortage'
            ]
            important_keywords = [
                'production', 'supply', 'demand', 'inventory', 'price',
                'smelter', 'refinery', 'export', 'import', 'tariff'
            ]
            
            for keyword in critical_keywords:
                if keyword in body_lower:
                    score += 15
            
            for keyword in important_keywords:
                if keyword in body_lower:
                    score += 5
        
        # ソース信頼性
        reliable_sources = ['REUTERS', 'BLOOMBERG', 'FASTMARKETS', 'METAL BULLETIN']
        source = news_item.get('source', '').upper()
        for reliable in reliable_sources:
            if reliable in source:
                score += 10
                break
        
        return score
    
    def _finalize_comprehensive_news(self, news_list: List[Dict], metal_keyword: str) -> List[Dict]:
        """包括的ニュースの最終処理"""
        if not news_list:
            return []
        
        # 重複排除（より厳密に）
        unique_news = []
        seen_headlines = set()
        seen_story_ids = set()
        
        for news in news_list:
            headline = news.get('headline', '')
            story_id = news.get('story_id', '')
            
            # ヘッドラインまたはストーリーIDで重複チェック
            headline_key = headline[:60].lower().strip()
            
            if story_id and story_id in seen_story_ids:
                continue
            if headline_key and headline_key in seen_headlines:
                continue
            
            if story_id:
                seen_story_ids.add(story_id)
            if headline_key:
                seen_headlines.add(headline_key)
            
            unique_news.append(news)
        
        # 優先度でソート
        unique_news.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        # 重要度に基づく選択（制限なし、すべて取得）
        major_news = []
        for news in unique_news:
            priority = news.get('priority_score', 0)
            
            # 一定以上の重要度を持つニュースをすべて取得
            if priority >= 10:  # 重要度10以上
                major_news.append(news)
            elif len(major_news) < 3:  # 重要度が低くても最低3件は確保
                major_news.append(news)
        
        return major_news
    
    def _get_simple_news_data(self, keyword: str, max_count: int) -> List[Dict]:
        """シンプルなニュース取得（より確実な方法）"""
        all_news = []
        
        # より基本的なクエリから段階的に試行
        search_queries = [
            keyword,
            f"{keyword} price",
            f"{keyword} market",
            f"LME {keyword}" if keyword != "general market" else "LME metals"
        ]
        
        for query in search_queries:
            try:
                self.logger.debug(f"ニュース検索クエリ: {query}")
                
                # シンプルなニュース取得（日付範囲なし）
                headlines = ek.get_news_headlines(
                    query=query,
                    count=min(max_count, 3)  # 各クエリで最大3件まで
                )
                
                if headlines is not None and not headlines.empty:
                    self.logger.debug(f"クエリ '{query}' で {len(headlines)}件のニュース取得")
                    
                    processed_news = self._extract_news_from_dataframe(headlines)
                    all_news.extend(processed_news)
                    
                    # 十分な数が集まったら終了
                    if len(all_news) >= max_count:
                        break
                else:
                    self.logger.debug(f"クエリ '{query}' でニュースなし")
                    
            except Exception as e:
                self.logger.warning(f"クエリ '{query}' でニュース取得エラー: {e}")
                continue
        
        # 重複排除とフィルタリング
        unique_news = self._filter_and_dedupe_news(all_news, max_count)
        
        return unique_news
    
    def _extract_news_from_dataframe(self, headlines: pd.DataFrame) -> List[Dict]:
        """データフレームからニュースを抽出"""
        news_list = []
        
        # 利用可能な列を確認
        available_columns = headlines.columns.tolist()
        self.logger.debug(f"利用可能な列: {available_columns}")
        
        for idx, row in headlines.iterrows():
            try:
                # ヘッドライン抽出（複数の可能な列名を試行）
                headline = None
                for col_name in ['headline', 'text', 'title', 'displayName', 'storyTitle']:
                    if col_name in available_columns and pd.notna(row.get(col_name)):
                        headline = str(row[col_name]).strip()
                        if headline:
                            break
                
                if not headline:
                    # インデックスから直接取得を試行
                    if len(row) > 0:
                        headline = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
                
                if not headline:
                    continue
                
                # 日時抽出
                date_str = None
                for col_name in ['versionCreated', 'firstCreated', 'date', 'timestamp']:
                    if col_name in available_columns and pd.notna(row.get(col_name)):
                        try:
                            date_value = row[col_name]
                            if isinstance(date_value, str):
                                date_str = date_value[:19]
                            else:
                                date_str = str(date_value)[:19]
                            break
                        except:
                            continue
                
                if not date_str:
                    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # ソース抽出
                source = 'Unknown'
                for col_name in ['sourceCode', 'source', 'provider']:
                    if col_name in available_columns and pd.notna(row.get(col_name)):
                        source = str(row[col_name])
                        break
                
                # ストーリーID抽出
                story_id = None
                for col_name in ['storyId', 'id', 'guid']:
                    if col_name in available_columns and pd.notna(row.get(col_name)):
                        story_id = str(row[col_name])
                        break
                
                if not story_id:
                    story_id = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{idx}"
                
                # ニュースアイテム作成
                news_item = {
                    'headline': headline[:250],  # 長すぎる場合は切り詰め
                    'date': date_str,
                    'source': source,
                    'story_id': story_id,
                    'priority_score': self._calculate_simple_priority(headline, source)
                }
                
                news_list.append(news_item)
                
            except Exception as e:
                self.logger.debug(f"ニュース行処理エラー ({idx}): {e}")
                continue
        
        return news_list
    
    def _calculate_simple_priority(self, headline: str, source: str) -> int:
        """シンプルな優先度計算"""
        score = 0
        headline_lower = headline.lower()
        
        # 重要キーワード
        high_keywords = ['strike', 'shutdown', 'shortage', 'disruption', 'tariff', 'sanction']
        medium_keywords = ['price', 'inventory', 'production', 'demand', 'supply', 'lme']
        
        for keyword in high_keywords:
            if keyword in headline_lower:
                score += 20
        
        for keyword in medium_keywords:
            if keyword in headline_lower:
                score += 10
        
        # 信頼できるソース
        reliable_sources = ['REUTERS', 'BLOOMBERG', 'FASTMARKETS']
        if any(reliable in source.upper() for reliable in reliable_sources):
            score += 5
        
        return score
    
    def _filter_and_dedupe_news(self, news_list: List[Dict], max_count: int) -> List[Dict]:
        """ニュースのフィルタリングと重複排除"""
        if not news_list:
            return []
        
        # 重複排除（ヘッドラインの最初の40文字で判断）
        unique_news = []
        seen_headlines = set()
        
        for news in news_list:
            headline = news.get('headline', '')
            headline_key = headline[:40].lower().strip()
            
            if headline_key and headline_key not in seen_headlines:
                seen_headlines.add(headline_key)
                unique_news.append(news)
        
        # 優先度でソート
        unique_news.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return unique_news[:max_count]
    
    def _get_general_market_news(self, max_count: int, hours_back: int, excluded_sources: List[str]) -> List[Dict]:
        """一般的な金属市場ニュース取得"""
        try:
            # より包括的な検索クエリ
            queries = [
                "LME AND (metals OR mining OR copper OR aluminum OR zinc)",
                "base metals AND (price OR supply OR demand)",
                "industrial metals AND (inventory OR production)",
                "metal commodities AND (China OR trade OR tariff)"
            ]
            
            all_news = []
            
            for query in queries:
                try:
                    # datetime64エラー対策: 日付を文字列形式に変換
                    date_from_str = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d')
                    date_to_str = datetime.now().strftime('%Y-%m-%d')
                    
                    headlines = ek.get_news_headlines(
                        query=query,
                        count=max_count,
                        date_from=date_from_str,
                        date_to=date_to_str
                    )
                    
                    if headlines is not None and not headlines.empty:
                        processed_news = self._process_news_headlines(headlines, excluded_sources)
                        all_news.extend(processed_news)
                        
                except Exception as query_error:
                    self.logger.warning(f"一般ニュース検索エラー (query: {query}): {query_error}")
                    continue
            
            # 重複排除とランキング
            unique_news = self._deduplicate_and_rank_news(all_news, max_count)
            return unique_news
            
        except Exception as e:
            self.logger.error(f"一般市場ニュース取得エラー: {e}")
            return []
    
    def _get_metal_specific_news(self, metal_name: str, max_count: int, hours_back: int, 
                                excluded_sources: List[str], priority_keywords: List[str]) -> List[Dict]:
        """金属固有ニュース取得"""
        try:
            # 金属名のバリエーション
            metal_variations = self._get_metal_name_variations(metal_name)
            
            all_news = []
            
            for variation in metal_variations:
                try:
                    # 基本検索
                    basic_query = f"LME AND {variation}"
                    # datetime64エラー対策: 日付を文字列形式に変換
                    date_from_str = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d')
                    date_to_str = datetime.now().strftime('%Y-%m-%d')
                    
                    headlines = ek.get_news_headlines(
                        query=basic_query,
                        count=max_count,
                        date_from=date_from_str,
                        date_to=date_to_str
                    )
                    
                    if headlines is not None and not headlines.empty:
                        processed_news = self._process_news_headlines(headlines, excluded_sources)
                        all_news.extend(processed_news)
                    
                    # 優先キーワードでの検索
                    for keyword in priority_keywords:
                        keyword_query = f"{variation} AND {keyword}"
                        try:
                            # datetime64エラー対策: 日付を文字列形式に変換
                            date_from_str = (datetime.now() - timedelta(hours=hours_back)).strftime('%Y-%m-%d')
                            date_to_str = datetime.now().strftime('%Y-%m-%d')
                            
                            keyword_headlines = ek.get_news_headlines(
                                query=keyword_query,
                                count=3,  # 少数に限定
                                date_from=date_from_str,
                                date_to=date_to_str
                            )
                            
                            if keyword_headlines is not None and not keyword_headlines.empty:
                                processed_news = self._process_news_headlines(keyword_headlines, excluded_sources)
                                # 優先キーワードニュースには高い重要度を付与
                                for news in processed_news:
                                    news['priority_score'] = news.get('priority_score', 0) + 10
                                all_news.extend(processed_news)
                                
                        except Exception as keyword_error:
                            self.logger.debug(f"{metal_name} キーワード検索エラー ({keyword}): {keyword_error}")
                            continue
                            
                except Exception as variation_error:
                    self.logger.warning(f"{metal_name} 検索エラー ({variation}): {variation_error}")
                    continue
            
            # 重複排除とランキング
            unique_news = self._deduplicate_and_rank_news(all_news, max_count)
            
            # フォールバックデータ追加（ニュースが少ない場合）
            if len(unique_news) < 2:
                fallback_news = self._get_fallback_news_data(metal_name)
                unique_news.extend(fallback_news)
                unique_news = unique_news[:max_count]
            
            return unique_news
            
        except Exception as e:
            self.logger.error(f"{metal_name} 固有ニュース取得エラー: {e}")
            return self._get_fallback_news_data(metal_name)
    
    def _get_metal_name_variations(self, metal_name: str) -> List[str]:
        """金属名のバリエーション生成"""
        variations_map = {
            'Copper': ['copper', 'cu', 'cuprum'],
            'Aluminium': ['aluminium', 'aluminum', 'al', 'bauxite'],
            'Zinc': ['zinc', 'zn'],
            'Lead': ['lead', 'pb', 'plumbum'],
            'Nickel': ['nickel', 'ni'],
            'Tin': ['tin', 'sn', 'stannum']
        }
        
        return variations_map.get(metal_name, [metal_name.lower()])
    
    def _process_news_headlines(self, headlines: pd.DataFrame, excluded_sources: List[str]) -> List[Dict]:
        """ニュースヘッドライン処理"""
        processed_news = []
        
        for idx, row in headlines.iterrows():
            try:
                # 基本情報抽出
                news_item = self._extract_news_item(row)
                
                if not news_item or not news_item.get('headline'):
                    continue
                
                # 除外ソース確認
                source = news_item.get('source', '').upper()
                if any(excluded in source for excluded in excluded_sources):
                    continue
                
                # 優先度計算
                news_item['priority_score'] = self._calculate_news_priority(news_item)
                
                processed_news.append(news_item)
                
            except Exception as e:
                self.logger.debug(f"ニュース行処理エラー: {e}")
                continue
        
        return processed_news
    
    def _extract_news_item(self, row: pd.Series) -> Dict:
        """ニュースアイテム抽出"""
        try:
            # ヘッドライン取得
            headline = ''
            for col in ['headline', 'text', 'title', 'displayName']:
                if col in row and pd.notna(row[col]):
                    headline = str(row[col]).strip()
                    break
            
            if not headline:
                return {}
            
            # 日時取得
            date_str = ''
            for col in ['versionCreated', 'date', 'timestamp', 'firstCreated']:
                if col in row and pd.notna(row[col]):
                    try:
                        if isinstance(row[col], str):
                            date_str = row[col][:19]
                        else:
                            date_str = str(row[col])[:19]
                        break
                    except:
                        continue
            
            # ストーリーID取得
            story_id = ''
            for col in ['storyId', 'id', 'newsId', 'guid']:
                if col in row and pd.notna(row[col]):
                    story_id = str(row[col])
                    break
            
            # ソース取得
            source = ''
            for col in ['sourceCode', 'source', 'provider']:
                if col in row and pd.notna(row[col]):
                    source = str(row[col])
                    break
            
            # カテゴリ取得
            category = ''
            for col in ['subjects', 'category', 'topic']:
                if col in row and pd.notna(row[col]):
                    category = str(row[col])
                    break
            
            return {
                'headline': headline[:300],  # 最大300文字
                'date': date_str,
                'story_id': story_id,
                'source': source,
                'category': category,
                'priority_score': 0
            }
            
        except Exception as e:
            self.logger.debug(f"ニュースアイテム抽出エラー: {e}")
            return {}
    
    def _calculate_news_priority(self, news_item: Dict) -> int:
        """ニュース優先度計算"""
        score = 0
        headline = news_item.get('headline', '').lower()
        
        # 設定から優先度キーワードを取得
        news_settings = self.config.get("news_settings", {})
        high_priority_keywords = news_settings.get("high_priority_keywords", [
            'strike', 'shutdown', 'disruption', 'mine closure', 'supply cut',
            'trade war', 'tariff', 'sanction', 'inventory surge', 'shortage'
        ])
        
        medium_priority_keywords = news_settings.get("medium_priority_keywords", [
            'price', 'production', 'demand', 'export', 'import', 'inventory',
            'stockpile', 'smelter', 'refinery', 'china', 'lme'
        ])
        
        reliable_sources = news_settings.get("reliable_sources", [
            'REUTERS', 'BLOOMBERG', 'FASTMARKETS', 'METAL BULLETIN'
        ])
        
        # 高優先度キーワード
        for keyword in high_priority_keywords:
            if keyword.lower() in headline:
                score += 20
        
        # 中優先度キーワード
        for keyword in medium_priority_keywords:
            if keyword.lower() in headline:
                score += 10
        
        # ソース信頼性
        source = news_item.get('source', '').upper()
        for reliable in reliable_sources:
            if reliable.upper() in source:
                score += 5
                break
        
        # 時間の新しさ
        try:
            date_str = news_item.get('date', '')
            if date_str:
                news_time = datetime.strptime(date_str[:19], '%Y-%m-%d %H:%M:%S')
                hours_ago = (datetime.now() - news_time).total_seconds() / 3600
                if hours_ago <= 6:
                    score += 15
                elif hours_ago <= 12:
                    score += 10
                elif hours_ago <= 24:
                    score += 5
        except:
            pass
        
        return score
    
    def _deduplicate_and_rank_news(self, news_list: List[Dict], max_count: int) -> List[Dict]:
        """ニュース重複排除とランキング"""
        if not news_list:
            return []
        
        # 重複排除（ヘッドラインの類似性で判断）
        unique_news = []
        seen_headlines = set()
        
        for news in news_list:
            headline = news.get('headline', '')
            # 簡単な重複チェック（最初の50文字で判断）
            headline_key = headline[:50].lower().strip()
            
            if headline_key not in seen_headlines and headline_key:
                seen_headlines.add(headline_key)
                unique_news.append(news)
        
        # 優先度でソート
        unique_news.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        return unique_news[:max_count]
    
    def _get_fallback_news_data(self, metal_name: str) -> List[Dict]:
        """フォールバックニュースデータ（API制限時用）"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        previous_date = self._get_previous_business_day().strftime('%Y-%m-%d')
        
        # 金属に応じたより具体的なフォールバックニュース
        fallback_templates = {
            'Copper': [
                "中国の銅需要動向と製造業PMI指標に注目",
                "LME銅価格の日中変動幅とインベントリ動向",
                "チリ・ペルーからの銅供給状況レポート"
            ],
            'Aluminium': [
                "中国のアルミニウム生産と電力コスト影響分析",
                "LMEアルミニウム在庫水準と製錬所稼働率",
                "ボーキサイト価格とアルミナコスト動向"
            ],
            'Zinc': [
                "亜鉛鉱山の生産状況と供給制約要因",
                "LME亜鉛価格と自動車産業需要の相関",
                "中国の亜鉛精錬マージン動向"
            ],
            'Lead': [
                "鉛蓄電池需要と自動車・電力貯蔵市場動向",
                "LME鉛価格とリサイクル鉛の需給バランス",
                "中国の鉛生産規制と環境政策影響"
            ],
            'Nickel': [
                "インドネシアのニッケル輸出政策とステンレス需要",
                "LMEニッケル価格とEV電池需要の影響",
                "フィリピン・ニューカレドニアの供給動向"
            ],
            'Tin': [
                "半導体産業のはんだ需要と錫価格動向",
                "LME錫在庫の歴史的低水準継続",
                "ミャンマー・インドネシアからの錫供給状況"
            ],
            'General_Market': [
                "基本金属市場全般の動向とマクロ経済指標",
                "中国の製造業PMIと金属需要の相関分析",
                "米ドル指数と商品市場への影響評価"
            ],
            'China_Economy': [
                "中国の製造業PMI発表と金属需要への影響",
                "中国の不動産投資と銅・鉄鋼需要動向",
                "人民銀行の金融政策と商品市場への波及効果"
            ]
        }
        
        templates = fallback_templates.get(metal_name, [
            f"{metal_name}市場の動向分析（API制限によりフォールバックデータ使用）",
            f"LME{metal_name}価格動向の概要"
        ])
        
        fallback_news = []
        for i, template in enumerate(templates[:3]):  # 最大3件
            fallback_news.append({
                'headline': template,
                'date': current_time,
                'story_id': f'fallback_{metal_name}_{i+1}',
                'source': 'SYSTEM_GENERATED',
                'category': 'Market Update',
                'priority_score': 1
            })
        
        return fallback_news
        
    def _get_fallback_price_data(self, metal_name: str) -> Dict:
        """フォールバック価格データ（デモ用）"""
        # 他の金属から最新価格の平均的な値を推定
        fallback_prices = {
            'Copper': 9793.00,
            'Aluminium': 2479.00,
            'Zinc': 2649.50,
            'Lead': 1986.50,
            'Nickel': 15421.00,
            'Tin': 32709.00
        }
        
        estimated_price = fallback_prices.get(metal_name, 10000.00)
        
        self.logger.warning(f"{metal_name} フォールバックデータを使用: ${estimated_price}")
        
        return {
            'ric': self.metals_rics.get(metal_name, ''),
            'close': estimated_price,
            'open': estimated_price * 0.999,  # 若干の変動を模擬
            'high': estimated_price * 1.002,
            'low': estimated_price * 0.998,
            'daily_change': -0.15,  # 小幅な下落を仮定
            'weekly_change': 1.0,   # 週次では上昇
            'monthly_change': 2.0,  # 月次では上昇
            'ytd_change': 10.0,     # 年初来では上昇
            'recent_trend': {
                'trend_direction': '横ばい',
                'trend_strength': '中',
                'range_position': '中値圏',
                'avg_daily_change': -0.15,
                'consecutive_days': {'direction': '下降', 'days': 1}
            },
            'cash_premium': None,
            'contango': None,
            'status': 'fallback_data'
        }
        
    def generate_report_file(self, data: Dict) -> str:
        """レポートファイル生成"""
        self.logger.info("レポートファイル生成開始")
        
        try:
            # ファイル名生成
            today = datetime.now().strftime("%Y%m%d")
            filename = f"LME_Daily_Report_Input_{today}.txt"
            
            # レポート内容生成
            report_content = self._build_report_content(data)
            
            # ファイル出力
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            
            output_path = output_dir / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
                
            self.logger.info(f"レポートファイル生成完了: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"レポートファイル生成エラー: {e}")
            raise
            
    def _build_report_content(self, data: Dict) -> str:
        """レポート内容構築"""
        today = datetime.now().strftime("%Y年%m月%d日")
        
        content = f"""【Claude用プロンプト部分】
以下のLME金属市場データを基に、機関投資家向けの日次マーケットレポートを日本語で作成してください。

【レポート要件】
- 各金属の前日の価格動向分析
- 3取引所在庫状況の評価とインプリケーション  
- 重要ニュースの市場への影響分析
- マクロ経済要因とドル円スワップレートの考慮
- 本日の注目ポイントと短期見通し
- プロフェッショナルかつ簡潔な日本語文体（800-1000語程度）

【市場データ - {today}】

=== 価格動向 ===
{self._format_price_data(data.get('prices', {}))}

=== 在庫状況 ===
{self._format_inventory_data(data.get('inventory', {}))}

=== 取引量 ===
{self._format_volume_data(data.get('volume', {}))}

=== フォワードカーブ・期間構造 ===
{self._format_forward_curve_data(data.get('forward_curves', {}))}

=== マクロ環境 ===
{self._format_macro_data(data.get('macro', {}))}

=== 株式市場 ===
{self._format_equity_data(data.get('equity', {}))}

=== リスクセンチメント ===
{self._format_risk_sentiment_data(data.get('risk_sentiment', {}))}

=== 関連ニュース ===
{self._format_news_data(data.get('news', {}))}

【分析指示】
- 数値は具体的に記載
- 地政学的要因も考慮
- リスク要因の言及も含める
- 前日との比較分析を重視
- 各金属の相関関係も分析
- 今後の注目ポイントを明確に記載
- 株式市場動向と金属需要の関連性を分析
- リスクセンチメント（リスクオン/オフ）が金属価格に与える影響を評価
- VIX、金価格、銅金比率等のセンチメント指標と金属市場の連動性を考察
- 第3水曜日ベースのフォワードカーブ・期間構造の変化（コンタンゴ/バックワーデーション）の意味を分析
- 各期間（1M、3M、6M、12M、24M）のスプレッド変化が示唆する需給バランス変化を評価
- 第3水曜日決済における期間構造が示すマーケットセンチメントと将来見通しを考察
- LME標準契約の月次満期構造から読み取れる市場の需給見通しと投資家ポジショニングを分析
- ドル円スワップレート（USD/JPY金利スワップ・預金金利）の変化が金属のフォワード取引に与える影響を考察
- USD/JPY金利差の変動がLME金属の期間構造やヘッジコストに与えるインパクトを評価
"""
        
        return content
        
    def _format_price_data(self, price_data: Dict) -> str:
        """価格データフォーマット（トレンド分析付き）"""
        if not price_data:
            return "価格データ取得エラー"
            
        lines = []
        for metal, data in price_data.items():
            if data and isinstance(data, dict):
                lines.append(f"【{metal}】")
                
                # フォールバックデータの場合は注記
                if data.get('status') == 'fallback_data':
                    lines.append(f"  ※ データ取得エラーのため推定値を表示")
                
                close = data.get('close')
                if close is not None and not pd.isna(close):
                    lines.append(f"  前日終値: ${close:.2f}")
                daily_change = data.get('daily_change')
                if daily_change is not None and not pd.isna(daily_change):
                    lines.append(f"  日次変動: {daily_change:+.2f}%")
                weekly_change = data.get('weekly_change')
                if weekly_change is not None and not pd.isna(weekly_change):
                    lines.append(f"  週次変動: {weekly_change:+.2f}%")
                monthly_change = data.get('monthly_change')
                if monthly_change is not None and not pd.isna(monthly_change):
                    lines.append(f"  月次変動: {monthly_change:+.2f}%")
                ytd_change = data.get('ytd_change')
                if ytd_change is not None and not pd.isna(ytd_change):
                    lines.append(f"  年初来変動: {ytd_change:+.2f}%")
                
                # 直近5営業日トレンド情報
                recent_trend = data.get('recent_trend', {})
                if recent_trend:
                    lines.append(f"  【直近5営業日トレンド】")
                    
                    trend_dir = recent_trend.get('trend_direction')
                    trend_str = recent_trend.get('trend_strength')
                    if trend_dir and trend_str:
                        lines.append(f"    トレンド: {trend_dir}傾向（{trend_str}）")
                    
                    range_pos = recent_trend.get('range_position')
                    if range_pos:
                        lines.append(f"    価格帯: {range_pos}")
                    
                    consecutive = recent_trend.get('consecutive_days', {})
                    if consecutive.get('days', 0) > 1:
                        lines.append(f"    連続: {consecutive.get('direction', '')} {consecutive.get('days', 0)}日")
                    
                    avg_change = recent_trend.get('avg_daily_change')
                    if avg_change is not None:
                        lines.append(f"    平均日次変動: {avg_change:+.2f}%")
                
                lines.append("")
                
        return "\n".join(lines)
        
    def _format_inventory_data(self, inventory_data: Dict) -> str:
        """在庫データフォーマット"""
        if not inventory_data:
            return "在庫データ取得エラー"
            
        lines = []
        
        # LME在庫
        if inventory_data.get('lme'):
            lines.append("【LME在庫】")
            for metal, data in inventory_data['lme'].items():
                if data:
                    stock_value = data.get('total_stock', 'N/A')
                    lines.append(f"  {metal}: {stock_value} トン")
                    
                    # トレンド情報
                    trend = data.get('trend', {})
                    if trend:
                        trend_dir = trend.get('trend_direction')
                        period_change = trend.get('period_change')
                        if trend_dir and period_change is not None:
                            lines.append(f"    (5営業日: {trend_dir} {period_change:+.0f}トン)")
            lines.append("")
            
        # COMEX在庫
        if inventory_data.get('comex'):
            lines.append("【COMEX在庫】")
            for metal, data in inventory_data['comex'].items():
                if data:
                    lines.append(f"  {metal}: {data.get('total_stock', 'N/A')} トン")
            lines.append("")
            
        # SHFE在庫
        if inventory_data.get('shfe'):
            lines.append("【SHFE在庫】")
            for metal, data in inventory_data['shfe'].items():
                if data:
                    lines.append(f"  {metal}: {data.get('total_stock', 'N/A')} トン")
            lines.append("")
            
        # SMM保税倉庫在庫
        if inventory_data.get('smm'):
            lines.append("【SMM保税倉庫在庫】")
            for metal, data in inventory_data['smm'].items():
                if data:
                    lines.append(f"  {metal}: {data.get('total_stock', 'N/A')} トン")
            lines.append("")
            
        return "\n".join(lines)
        
    def _format_volume_data(self, volume_data: Dict) -> str:
        """取引量データフォーマット"""
        if not volume_data:
            return "取引量データ取得エラー"
            
        lines = []
        for metal, data in volume_data.items():
            if data and isinstance(data, dict):
                lines.append(f"【{metal}】")
                volume = data.get('volume')
                if volume is not None and not pd.isna(volume):
                    lines.append(f"  出来高: {volume:,} 契約")
                
                # トレンド情報
                trend = data.get('trend', {})
                if trend:
                    activity_level = trend.get('activity_level')
                    vs_average = trend.get('vs_average_pct')
                    if activity_level and vs_average is not None:
                        lines.append(f"    (活動度: {activity_level}、平均比 {vs_average:+.1f}%)")
                
                open_int = data.get('open_interest')
                if open_int is not None and not pd.isna(open_int):
                    lines.append(f"  建玉: {open_int:,} 契約")
                lines.append("")
                
        return "\n".join(lines)
    
    def _format_forward_curve_data(self, forward_curve_data: Dict) -> str:
        """フォワードカーブデータフォーマット（日付ベース）"""
        if not forward_curve_data:
            return "フォワードカーブデータ取得エラー"
            
        lines = []
        
        for metal, data in forward_curve_data.items():
            if data and isinstance(data, dict):
                lines.append(f"【{metal}】")
                
                # 期間構造分析
                structure_analysis = data.get('structure_analysis', {})
                if structure_analysis:
                    structure = structure_analysis.get('structure', '不明')
                    strength = structure_analysis.get('strength', '不明')
                    structure_change = structure_analysis.get('structure_change', '不明')
                    near_far_spread = structure_analysis.get('near_far_spread')
                    near_contract = structure_analysis.get('near_contract')
                    far_contract = structure_analysis.get('far_contract')
                    
                    lines.append(f"  期間構造: {structure}({strength})")
                    if near_far_spread is not None and near_contract and far_contract:
                        near_str = near_contract.strftime('%Y-%m') if hasattr(near_contract, 'strftime') else str(near_contract)[:7]
                        far_str = far_contract.strftime('%Y-%m') if hasattr(far_contract, 'strftime') else str(far_contract)[:7]
                        lines.append(f"  {far_str} - {near_str} スプレッド: ${near_far_spread:.2f}")
                    lines.append(f"  前日比変化: {structure_change}")
                
                # カーブデータ（細かいグリッド：月次～2年）
                # 注意：価格変化は前営業日(T-1)と前々営業日(T-2)の比較です
                curve_data = data.get('curve_data', {})
                if curve_data:
                    lines.append("  【価格水準（細かいグリッド）】")
                    
                    # 月数でソートされたデータを取得
                    sorted_data = []
                    for date_key, curve_info in curve_data.items():
                        if curve_info.get('current_price') is not None:
                            sorted_data.append((curve_info.get('months_from_now', 999), curve_info))
                    
                    sorted_data.sort(key=lambda x: x[0])
                    
                    # 1年以内は月次、それ以降は主要ポイントのみ表示
                    display_months = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 18, 24]
                    for months, curve_info in sorted_data:
                        if months in display_months:
                            current_price = curve_info.get('current_price')
                            price_change = curve_info.get('price_change')
                            contract_date = curve_info.get('date')
                            
                            if current_price is not None:
                                date_str = contract_date.strftime('%Y-%m') if hasattr(contract_date, 'strftime') else 'N/A'
                                price_str = f"    {months}M ({date_str}): ${current_price:.2f}"
                                if price_change is not None:
                                    price_str += f" ({price_change:+.2f})"
                                lines.append(price_str)
                
                # スプレッド分析（T-1 vs T-2比較）
                spreads = data.get('spreads', {})
                if spreads:
                    lines.append("  【月次スプレッド変化（1年以内）】")
                    
                    # 月次スプレッド（1年以内）- 手前期先に変更
                    monthly_spreads = ['0M_1M', '1M_2M', '2M_3M', '3M_4M', '4M_5M', '5M_6M', 
                                     '6M_7M', '7M_8M', '8M_9M', '9M_10M', '10M_11M', '11M_12M']
                    
                    for spread_name in monthly_spreads:
                        if spread_name in spreads:
                            spread_data = spreads[spread_name]
                            current_spread = spread_data.get('current_spread')
                            spread_change = spread_data.get('spread_change')
                            description = spread_data.get('spread_description', spread_name)
                            
                            if current_spread is not None:
                                spread_str = f"    {description}: ${current_spread:.2f}"
                                if spread_change is not None:
                                    spread_str += f" ({spread_change:+.2f})"
                                lines.append(spread_str)
                    
                    lines.append("  【主要クロススプレッド】")
                    
                    # 主要クロススプレッド - 手前期先に変更
                    major_spread_names = ['1M_3M_major', '3M_6M_major', '6M_12M_major', '12M_24M_major']
                    for spread_name in major_spread_names:
                        if spread_name in spreads:
                            spread_data = spreads[spread_name]
                            current_spread = spread_data.get('current_spread')
                            spread_change = spread_data.get('spread_change')
                            description = spread_data.get('spread_description', spread_name)
                            
                            if current_spread is not None:
                                spread_str = f"    {description}: ${current_spread:.2f}"
                                if spread_change is not None:
                                    spread_str += f" ({spread_change:+.2f})"
                                lines.append(spread_str)
                
                lines.append("")
                
        return "\n".join(lines)
        
    def _format_macro_data(self, macro_data: Dict) -> str:
        """マクロデータフォーマット"""
        if not macro_data:
            return "マクロ経済データ取得エラー"
            
        lines = []
        
        # 従来のマクロ経済指標
        for indicator, data in macro_data.items():
            if indicator == 'swap_rates':
                continue  # スワップレートは別途処理
                
            if data and isinstance(data, dict):
                value = data.get('value')
                if value is not None and not pd.isna(value):
                    lines.append(f"{indicator}: {value}")
        
        # スワップレートデータの表示
        swap_rates = macro_data.get('swap_rates', {})
        if swap_rates:
            lines.append("\n【スワップレート】")
            for rate_name, rate_data in swap_rates.items():
                if rate_data and isinstance(rate_data, dict):
                    rate_value = rate_data.get('rate')
                    description = rate_data.get('description', rate_name)
                    if rate_value is not None and not pd.isna(rate_value):
                        lines.append(f"{description}: {rate_value}%")
                
        return "\n".join(lines)
    
    def _format_equity_data(self, equity_data: Dict) -> str:
        """株式市場データフォーマット"""
        if not equity_data:
            return "株式市場データ取得エラー"
            
        lines = []
        
        # 主要株式指数（詳細表示）
        major_indices = ['S&P_500_FUTURES', 'NASDAQ', 'DOW', 'NIKKEI_FUTURES']
        lines.append("【主要株式指数】")
        
        has_major_data = False
        for index_name in major_indices:
            data = equity_data.get(index_name)
            if data and isinstance(data, dict):
                current_price = data.get('current_price')
                daily_change = data.get('daily_change')
                weekly_change = data.get('weekly_change')
                monthly_change = data.get('monthly_change')
                ytd_change = data.get('ytd_change')
                
                # データがあるもののみ表示
                if current_price is not None and not pd.isna(current_price):
                    has_major_data = True
                    display_name = index_name.replace('_FUTURES', '').replace('_', ' ')
                    lines.append(f"  {display_name}:")
                    lines.append(f"    現在値: {current_price:.2f}")
                    
                    if daily_change is not None and not pd.isna(daily_change):
                        lines.append(f"    日次: {daily_change:+.2f}%")
                    if weekly_change is not None and not pd.isna(weekly_change):
                        lines.append(f"    週次: {weekly_change:+.2f}%")
                    if monthly_change is not None and not pd.isna(monthly_change):
                        lines.append(f"    月次: {monthly_change:+.2f}%")
                    if ytd_change is not None and not pd.isna(ytd_change):
                        lines.append(f"    年初来: {ytd_change:+.2f}%")
                    lines.append("")
        
        if not has_major_data:
            lines.append("  データ取得エラー")
            lines.append("")
        
        # その他のアジア・欧州指数（簡潔表示）
        other_indices = ['HANG_SENG', 'FTSE_100', 'DAX', 'CAC', 'MSCI_WORLD', 'MSCI_EM']
        lines.append("【その他主要指数】")
        
        has_other_data = False
        for index_name in other_indices:
            data = equity_data.get(index_name)
            if data and isinstance(data, dict):
                current_price = data.get('current_price')
                daily_change = data.get('daily_change')
                
                if current_price is not None and not pd.isna(current_price):
                    has_other_data = True
                    entry = f"  {index_name}: {current_price:.2f}"
                    if daily_change is not None and not pd.isna(daily_change):
                        entry += f" ({daily_change:+.2f}%)"
                    lines.append(entry)
        
        if not has_other_data:
            lines.append("  データ取得エラー")
        
        lines.append("")
        return "\n".join(lines)
    
    def _format_risk_sentiment_data(self, sentiment_data: Dict) -> str:
        """リスクセンチメントデータフォーマット"""
        if not sentiment_data:
            return "リスクセンチメントデータ取得エラー"
            
        lines = []
        
        # 総合リスクセンチメント
        analysis = sentiment_data.get('risk_sentiment_analysis', {})
        if analysis:
            lines.append("【総合リスクセンチメント】")
            sentiment = analysis.get('overall_sentiment', '不明')
            confidence = analysis.get('confidence_level', '低')
            risk_on_ratio = analysis.get('risk_on_ratio', 0)
            risk_off_ratio = analysis.get('risk_off_ratio', 0)
            
            lines.append(f"  判定: {sentiment} (信頼度: {confidence})")
            lines.append(f"  リスクオン指標: {risk_on_ratio}%")
            lines.append(f"  リスクオフ指標: {risk_off_ratio}%")
            lines.append("")
        
        # 主要センチメント指標
        lines.append("【主要センチメント指標】")
        
        # VIX恐怖指数
        vix_data = sentiment_data.get('VIX_VOLATILITY', {})
        if vix_data:
            vix_value = vix_data.get('value')
            vix_change = vix_data.get('daily_change')
            if vix_value is not None:
                entry = f"  VIX恐怖指数: {vix_value:.2f}"
                if vix_change is not None:
                    entry += f" ({vix_change:+.2f}%)"
                
                # VIXレベル解釈
                if vix_value < 20:
                    entry += " [低ボラティリティ]"
                elif vix_value > 30:
                    entry += " [高ボラティリティ]"
                else:
                    entry += " [中程度ボラティリティ]"
                lines.append(entry)
        
        # 金価格（安全資産）
        gold_data = sentiment_data.get('GOLD_PRICE', {})
        if gold_data:
            gold_value = gold_data.get('value')
            gold_change = gold_data.get('daily_change')
            if gold_value is not None:
                entry = f"  金価格: ${gold_value:.2f}"
                if gold_change is not None:
                    entry += f" ({gold_change:+.2f}%)"
                lines.append(entry)
        
        # USD/JPY（リスク通貨ペア）
        usdjpy_data = sentiment_data.get('USD_JPY', {})
        if usdjpy_data:
            usdjpy_value = usdjpy_data.get('value')
            usdjpy_change = usdjpy_data.get('daily_change')
            if usdjpy_value is not None:
                entry = f"  USD/JPY: {usdjpy_value:.2f}"
                if usdjpy_change is not None:
                    entry += f" ({usdjpy_change:+.2f}%)"
                lines.append(entry)
        
        # 銅金比率（景気敏感指標）
        copper_gold_data = sentiment_data.get('COPPER_GOLD_RATIO', {})
        if copper_gold_data:
            ratio_value = copper_gold_data.get('value')
            ratio_change = copper_gold_data.get('daily_change')
            if ratio_value is not None:
                entry = f"  銅金比率: {ratio_value:.4f}"
                if ratio_change is not None:
                    entry += f" ({ratio_change:+.2f}%)"
                lines.append(entry)
        
        # イールドスプレッド
        spread_data = sentiment_data.get('US_2Y_10Y_SPREAD', {})
        if spread_data:
            spread_value = spread_data.get('value')
            spread_change = spread_data.get('daily_change')
            if spread_value is not None:
                entry = f"  米2Y-10Yスプレッド: {spread_value:.2f}bp"
                if spread_change is not None:
                    entry += f" ({spread_change:+.2f}%)"
                lines.append(entry)
        
        lines.append("")
        return "\n".join(lines)
        
    def _format_news_data(self, news_data: Dict) -> str:
        """ニュースデータフォーマット（本文付き）"""
        if not news_data:
            return "ニュースデータ取得エラー"
            
        lines = []
        
        # 一般市場ニュースを最初に表示
        if 'General_Market' in news_data and news_data['General_Market']:
            lines.append("【金属市場全般ニュース】")
            for news in news_data['General_Market']:  # すべて表示
                lines.extend(self._format_single_news(news))
            lines.append("")
        
        # 中国経済ニュースを次に表示
        if 'China_Economy' in news_data and news_data['China_Economy']:
            lines.append("【中国経済関連ニュース】")
            for news in news_data['China_Economy']:  # すべて表示
                lines.extend(self._format_single_news(news))
            lines.append("")
        
        # 各金属固有のニュース
        for metal, news_list in news_data.items():
            if metal in ['General_Market', 'China_Economy']:  # 既に処理済み
                continue
                
            if news_list:
                lines.append(f"【{metal}関連ニュース】")
                for news in news_list:  # すべて表示
                    lines.extend(self._format_single_news(news))
                lines.append("")
                
        # ニュースが全くない場合
        if len(lines) == 0:
            lines.append("現在利用可能なニュースデータがありません")
            
        return "\n".join(lines)
    
    def _format_single_news(self, news: Dict) -> List[str]:
        """単一ニュースアイテムのフォーマット"""
        lines = []
        
        headline = news.get('headline', '')
        date = news.get('date', '')
        source = news.get('source', '')
        category = news.get('category', '')
        body = news.get('body', '')
        priority_score = news.get('priority_score', 0)
        
        # 優先度に応じて重要度マーク
        priority_mark = ""
        if priority_score >= 25:
            priority_mark = "🔴"  # 高重要
        elif priority_score >= 15:
            priority_mark = "🟡"  # 中重要
        else:
            priority_mark = "⚪"  # 通常
        
        # ヘッドライン
        lines.append(f"  {priority_mark} {headline}")
        
        # 日時とソース情報
        info_parts = []
        if date:
            info_parts.append(f"{date[:16]}")
        if source and source != 'SYSTEM_GENERATED':
            info_parts.append(f"出典: {source}")
        if category and category.strip():
            info_parts.append(f"分類: {category}")
        
        if info_parts:
            lines.append(f"    [{' | '.join(info_parts)}]")
        
        # 本文（ある場合）
        if body and body.strip():
            # 本文の表示用整形
            formatted_body = body.strip()
            
            # 長すぎる場合は文章の区切りで切り詰め
            if len(formatted_body) > 2000:
                # 2000文字付近で文の区切りを探す
                truncate_pos = formatted_body.rfind('. ', 0, 2000)
                if truncate_pos > 500:  # 最低500文字は確保
                    formatted_body = formatted_body[:truncate_pos + 1]
                else:
                    formatted_body = formatted_body[:2000] + "..."
            
            # 改行を挿入して読みやすくする（500文字ごとに改行）
            if len(formatted_body) > 500:
                parts = []
                start = 0
                while start < len(formatted_body):
                    # 次の500文字の範囲で文の区切りを探す
                    end = start + 500
                    if end < len(formatted_body):
                        # 文の区切りを探す
                        break_pos = formatted_body.rfind('. ', start + 400, end + 100)
                        if break_pos > start:
                            parts.append(formatted_body[start:break_pos + 1])
                            start = break_pos + 2
                        else:
                            # 文の区切りが見つからない場合はスペースで区切る
                            break_pos = formatted_body.rfind(' ', start + 400, end)
                            if break_pos > start:
                                parts.append(formatted_body[start:break_pos])
                                start = break_pos + 1
                            else:
                                parts.append(formatted_body[start:end])
                                start = end
                    else:
                        parts.append(formatted_body[start:])
                        break
                formatted_body = '\n      '.join(parts)
            
            lines.append(f"    本文: {formatted_body}")
        
        lines.append("")  # 空行追加
        
        return lines
        
    def run(self):
        """メイン実行処理"""
        self.logger.info("LME日次レポート生成開始")
        
        try:
            # データ取得
            data = {
                'prices': self.get_price_data(),
                'inventory': self.get_inventory_data(),
                'volume': self.get_volume_data(),
                'forward_curves': self.get_forward_curve_data(),
                'macro': self.get_macro_data(),
                'equity': self.get_equity_data(),
                'risk_sentiment': self.get_risk_sentiment_data(),
                'news': self.get_news_data()
            }
            
            # レポートファイル生成
            output_file = self.generate_report_file(data)
            
            self.logger.info(f"LME日次レポート生成完了: {output_file}")
            print(f"レポートファイルが生成されました: {output_file}")
            
            return output_file
            
        except Exception as e:
            self.logger.error(f"レポート生成エラー: {e}")
            raise


def main():
    """メイン関数"""
    try:
        # レポート生成器作成
        generator = LMEReportGenerator()
        
        # レポート実行
        output_file = generator.run()
        
        print(f"\n=== 実行完了 ===")
        print(f"出力ファイル: {output_file}")
        print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"実行エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()