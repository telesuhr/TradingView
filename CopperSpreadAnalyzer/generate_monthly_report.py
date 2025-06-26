#!/usr/bin/env python3
"""
LME Copper スプレッド取引データ月次レポート生成
取得済みデータを集計して分析レポートを作成
"""

import os
import pandas as pd
from datetime import datetime, timedelta
import glob
import logging

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/monthly_report.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def find_available_data_files():
    """利用可能なデータファイルを検索"""
    summary_files = glob.glob('output/copper_spread_summary_minute_jst_*.csv')
    trades_files = glob.glob('output/copper_spread_trades_minute_jst_*.csv')
    
    summary_dates = [os.path.basename(f).replace('copper_spread_summary_minute_jst_', '').replace('.csv', '') 
                     for f in summary_files]
    trades_dates = [os.path.basename(f).replace('copper_spread_trades_minute_jst_', '').replace('.csv', '')
                    for f in trades_files]
    
    # 両方のファイルが揃っている日付のみ
    available_dates = list(set(summary_dates) & set(trades_dates))
    available_dates.sort()
    
    return available_dates

def load_all_summary_data(available_dates):
    """全サマリーデータを統合"""
    all_summaries = []
    
    for date_str in available_dates:
        file_path = f'output/copper_spread_summary_minute_jst_{date_str}.csv'
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            all_summaries.append(df)
        except Exception as e:
            print(f"エラー: {date_str} - {e}")
            continue
    
    if all_summaries:
        combined_df = pd.concat(all_summaries, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()

def load_all_trades_data(available_dates):
    """全取引データを統合（サンプルのみ）"""
    all_trades = []
    
    for date_str in available_dates:
        file_path = f'output/copper_spread_trades_minute_jst_{date_str}.csv'
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            # メモリ節約のため最初の1000件のみ
            all_trades.append(df.head(1000))
        except Exception as e:
            print(f"エラー: {date_str} - {e}")
            continue
    
    if all_trades:
        combined_df = pd.concat(all_trades, ignore_index=True)
        return combined_df
    else:
        return pd.DataFrame()

def analyze_summary_data(summary_df, logger):
    """サマリーデータの分析"""
    logger.info("\n" + "="*60)
    logger.info("LME銅スプレッド取引 月次分析レポート")
    logger.info("="*60)
    
    if summary_df.empty:
        logger.warning("分析対象データが見つかりません")
        return
    
    # 基本統計
    total_days = summary_df['trade_date'].nunique()
    total_spreads = len(summary_df)
    unique_rics = summary_df['spread_ric'].nunique()
    total_trades = summary_df['trade_count'].sum()
    total_volume = summary_df['total_volume'].sum()
    
    logger.info(f"\n=== 基本統計 ===")
    logger.info(f"分析期間: {summary_df['trade_date'].min()} ～ {summary_df['trade_date'].max()}")
    logger.info(f"営業日数: {total_days}日")
    logger.info(f"総スプレッド記録: {total_spreads:,}件")
    logger.info(f"ユニークスプレッド: {unique_rics}種類")
    logger.info(f"総取引回数: {total_trades:,}回")
    logger.info(f"総取引量: {total_volume:,.0f}ロット")
    
    # 日別統計
    daily_stats = summary_df.groupby('trade_date').agg({
        'spread_ric': 'count',
        'trade_count': 'sum',
        'total_volume': 'sum'
    }).rename(columns={'spread_ric': 'active_spreads'})
    
    logger.info(f"\n=== 日別平均 ===")
    logger.info(f"1日平均アクティブスプレッド: {daily_stats['active_spreads'].mean():.1f}個")
    logger.info(f"1日平均取引回数: {daily_stats['trade_count'].mean():.0f}回")
    logger.info(f"1日平均取引量: {daily_stats['total_volume'].mean():.0f}ロット")
    
    # スプレッド別統計（上位15個）
    spread_stats = summary_df.groupby('spread_ric').agg({
        'trade_count': 'sum',
        'total_volume': 'sum',
        'trade_date': 'count'
    }).rename(columns={'trade_date': 'trading_days'})
    spread_stats = spread_stats.sort_values('total_volume', ascending=False)
    
    logger.info(f"\n=== 取引量上位スプレッド（Top 15） ===")
    for i, (ric, data) in enumerate(spread_stats.head(15).iterrows()):
        logger.info(f"{i+1:2d}. {ric:20s}: {data['total_volume']:8.0f}ロット ({data['trading_days']:2d}日, {data['trade_count']:4d}取引)")
    
    # 期間構造別分析
    logger.info(f"\n=== スプレッド種別分析 ===")
    
    # Cash vs 他
    cash_spreads = summary_df[summary_df['near_leg'] == 'Cash']
    cash_volume = cash_spreads['total_volume'].sum()
    logger.info(f"Cashスプレッド: {len(cash_spreads):3d}件 ({cash_volume:8.0f}ロット)")
    
    # 3Month vs 他
    three_month_spreads = summary_df[summary_df['near_leg'] == '3Month']
    three_month_volume = three_month_spreads['total_volume'].sum()
    logger.info(f"3Monthスプレッド: {len(three_month_spreads):3d}件 ({three_month_volume:8.0f}ロット)")
    
    # 限月間スプレッド
    contract_spreads = summary_df[~summary_df['near_leg'].isin(['Cash', '3Month'])]
    contract_volume = contract_spreads['total_volume'].sum()
    logger.info(f"限月間スプレッド: {len(contract_spreads):3d}件 ({contract_volume:8.0f}ロット)")
    
    # 取引時間分析（サンプルデータから）
    logger.info(f"\n=== 日別取引状況 ===")
    for date in daily_stats.index:
        day_data = daily_stats.loc[date]
        logger.info(f"{date}: {day_data['active_spreads']:2d}スプレッド, {day_data['trade_count']:4d}取引, {day_data['total_volume']:6.0f}ロット")

def generate_csv_report(summary_df, available_dates):
    """CSV形式でレポート出力"""
    if summary_df.empty:
        return
    
    # スプレッド別集計
    spread_report = summary_df.groupby('spread_ric').agg({
        'trade_count': 'sum',
        'total_volume': 'sum',
        'trade_date': 'count',
        'price_min': 'min',
        'price_max': 'max',
        'near_leg': 'first',
        'far_leg': 'first'
    }).rename(columns={'trade_date': 'trading_days'}).sort_values('total_volume', ascending=False)
    
    # ファイル名
    start_date = available_dates[0]
    end_date = available_dates[-1]
    report_filename = f'output/copper_spread_monthly_report_{start_date}_to_{end_date}.csv'
    
    spread_report.to_csv(report_filename, encoding='utf-8-sig')
    print(f"\n月次レポートを保存: {report_filename}")
    
    # 日別サマリー
    daily_report = summary_df.groupby('trade_date').agg({
        'spread_ric': 'count',
        'trade_count': 'sum',
        'total_volume': 'sum'
    }).rename(columns={'spread_ric': 'active_spreads'})
    
    daily_filename = f'output/copper_spread_daily_summary_{start_date}_to_{end_date}.csv'
    daily_report.to_csv(daily_filename, encoding='utf-8-sig')
    print(f"日別サマリーを保存: {daily_filename}")

def main():
    """メイン実行"""
    logger = setup_logging()
    logger.info("月次レポート生成開始")
    
    # 利用可能なデータファイルを検索
    available_dates = find_available_data_files()
    
    if not available_dates:
        logger.error("利用可能なデータファイルが見つかりません")
        return
    
    logger.info(f"利用可能データ: {len(available_dates)}日分")
    logger.info(f"期間: {available_dates[0]} ～ {available_dates[-1]}")
    
    # データ読み込み
    summary_df = load_all_summary_data(available_dates)
    
    # 分析実行
    analyze_summary_data(summary_df, logger)
    
    # CSVレポート生成
    generate_csv_report(summary_df, available_dates)
    
    logger.info("月次レポート生成完了")

if __name__ == "__main__":
    main()