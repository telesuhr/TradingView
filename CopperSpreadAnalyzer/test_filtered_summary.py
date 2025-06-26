#!/usr/bin/env python3
"""
取引があったスプレッドのみのサマリー生成テスト
"""

import pandas as pd
import sys
import os

def filter_summary_data():
    """既存のサマリーファイルから取引があったもののみをフィルタリング"""
    
    # 既存のサマリーファイルを読み込み
    summary_file = "output/copper_spread_summary_minute_jst_2025-06-17.csv"
    
    if not os.path.exists(summary_file):
        print("サマリーファイルが見つかりません")
        return
    
    # CSVファイル読み込み
    df = pd.read_csv(summary_file)
    
    print(f"全データ数: {len(df)}")
    print("\nステータス別件数:")
    print(df['status'].value_counts())
    
    # 取引があったもののみフィルタリング
    trades_only = df[df['status'] == 'success_with_trades'].copy()
    
    print(f"\n取引があったスプレッド: {len(trades_only)}個")
    
    # フィルタ済みファイルを保存
    filtered_file = "output/copper_spread_summary_trades_only_2025-06-17.csv"
    trades_only.to_csv(filtered_file, index=False, encoding='utf-8-sig')
    print(f"フィルタ済みサマリーを保存: {filtered_file}")
    
    # 取引量順に表示
    trades_sorted = trades_only.sort_values('total_volume', ascending=False)
    
    print(f"\n=== 取引量上位スプレッド ===")
    for i, row in trades_sorted.head(10).iterrows():
        print(f"{len(trades_sorted) - trades_sorted.index.get_loc(i):2d}. {row['spread_ric']:18s}: {row['total_volume']:6.0f}ロット ({row['trade_count']:3d}取引)")

if __name__ == "__main__":
    filter_summary_data()