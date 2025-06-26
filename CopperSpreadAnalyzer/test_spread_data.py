#!/usr/bin/env python3
"""
LME Copper Spread取引データ取得テスト
対象: Cash-Jul25 (CMCU0-N25)
"""

import eikon as ek
import pandas as pd
import json
from datetime import datetime, timedelta
import logging
import sys
import os

# 親ディレクトリの設定ファイルを読み込み
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/spread_test.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def load_config():
    """設定ファイル読み込み"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        print(f"探索パス: {config_path}")
        return None

def test_spread_ric_data(logger):
    """Cash-Jul25スプレッドデータ取得テスト"""
    
    # テスト対象RIC
    spread_ric = "CMCU0-N25"  # Cash-Jul25
    logger.info(f"テスト対象RIC: {spread_ric}")
    
    # 前営業日を計算
    today = datetime.now()
    previous_business_day = today - timedelta(days=1)
    while previous_business_day.weekday() >= 5:  # 土日をスキップ
        previous_business_day -= timedelta(days=1)
    
    date_str = previous_business_day.strftime('%Y-%m-%d')
    logger.info(f"取得対象日: {date_str}")
    
    # テスト1: 基本的な価格データ取得
    logger.info("=== テスト1: 基本価格データ取得 ===")
    try:
        basic_fields = ['CF_LAST', 'CF_VOLUME', 'CF_DATE', 'CF_TIME']
        df_basic, err = ek.get_data(spread_ric, basic_fields)
        
        if err:
            logger.warning(f"基本データ取得警告: {err}")
        
        if df_basic is not None and not df_basic.empty:
            logger.info("基本データ取得成功:")
            logger.info(f"\n{df_basic}")
        else:
            logger.warning("基本データが空です")
            
    except Exception as e:
        logger.error(f"基本データ取得エラー: {e}")
    
    # テスト2: 時系列データ取得
    logger.info("\n=== テスト2: 時系列データ取得 ===")
    try:
        ts_fields = ['CLOSE', 'VOLUME', 'HIGH', 'LOW']
        df_timeseries = ek.get_timeseries(
            spread_ric, 
            fields=ts_fields,
            start_date=date_str,
            end_date=date_str
        )
        
        if df_timeseries is not None and not df_timeseries.empty:
            logger.info("時系列データ取得成功:")
            logger.info(f"\n{df_timeseries}")
        else:
            logger.warning("時系列データが空です")
            
    except Exception as e:
        logger.error(f"時系列データ取得エラー: {e}")
    
    # テスト3: 詳細取引データ取得試行
    logger.info("\n=== テスト3: 詳細取引データ取得試行 ===")
    
    # 取引データ用フィールドのテスト
    trade_fields_sets = [
        # セット1: 基本取引情報
        ['TR.TRADEPRICE', 'TR.TRADEVOLUME', 'TR.TRADETIME', 'TR.TRADEDATE'],
        # セット2: より詳細な取引情報
        ['TR.PriceClose', 'TR.Volume', 'TR.PriceHigh', 'TR.PriceLow'],
        # セット3: オルタナティブフィールド
        ['TRDPRC_1', 'TRDVOL_1', 'TRADE_DATE', 'NUM_MOVES'],
        # セット4: 一般的なフィールド
        ['LAST', 'ACVOL_1', 'HST_CLOSE', 'QUOTIM']
    ]
    
    for i, fields in enumerate(trade_fields_sets, 1):
        logger.info(f"\n--- フィールドセット{i}: {fields} ---")
        try:
            df_trade, err = ek.get_data(spread_ric, fields)
            
            if err:
                logger.warning(f"取引データ取得警告: {err}")
            
            if df_trade is not None and not df_trade.empty:
                logger.info("取引データ取得成功:")
                logger.info(f"\n{df_trade}")
                
                # CSVで保存
                output_file = f"output/spread_test_set{i}_{date_str}.csv"
                df_trade.to_csv(output_file, index=False, encoding='utf-8-sig')
                logger.info(f"データを保存: {output_file}")
            else:
                logger.warning("取引データが空です")
                
        except Exception as e:
            logger.error(f"取引データ取得エラー: {e}")
    
    # テスト4: データ取得可能フィールドの探索
    logger.info("\n=== テスト4: 利用可能フィールド探索 ===")
    try:
        # よく使われるフィールド名のテスト
        common_fields = [
            'OPEN_PRC', 'HIGH_1', 'LOW_1', 'CLOSE_BID', 'CLOSE_ASK',
            'BID', 'ASK', 'BIDSIZE', 'ASKSIZE', 'SPREAD',
            'CF_BID', 'CF_ASK', 'CF_CLOSE', 'CF_OPEN'
        ]
        
        logger.info(f"テストフィールド: {common_fields}")
        df_common, err = ek.get_data(spread_ric, common_fields)
        
        if err:
            logger.warning(f"一般フィールド取得警告: {err}")
        
        if df_common is not None and not df_common.empty:
            logger.info("一般フィールドデータ取得成功:")
            logger.info(f"\n{df_common}")
            
            # 値が存在するフィールドのみを特定
            non_null_fields = []
            for col in df_common.columns:
                if col != 'Instrument' and not df_common[col].isna().all():
                    non_null_fields.append(col)
            
            logger.info(f"データが存在するフィールド: {non_null_fields}")
        else:
            logger.warning("一般フィールドデータが空です")
            
    except Exception as e:
        logger.error(f"一般フィールド取得エラー: {e}")

def main():
    """メイン実行"""
    logger = setup_logging()
    logger.info("LME Copper Spread取引データ取得テスト開始")
    
    # 設定読み込み
    config = load_config()
    if not config:
        logger.error("設定ファイルの読み込みに失敗しました")
        return
    
    # EIKON API初期化
    try:
        api_key = config.get('eikon_api_key')
        if not api_key:
            logger.error("EIKON APIキーが設定されていません")
            return
        
        ek.set_app_key(api_key)
        logger.info("EIKON API初期化完了")
        
    except Exception as e:
        logger.error(f"EIKON API初期化エラー: {e}")
        return
    
    # スプレッドデータ取得テスト実行
    test_spread_ric_data(logger)
    
    logger.info("テスト完了")

if __name__ == "__main__":
    main()