#!/usr/bin/env python3
"""
上海銅プレミアム市場代表性と特性分析
"""

import sys
import json
import eikon as ek
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def load_config():
    """設定ファイル読み込み"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

def analyze_market_characteristics():
    """市場代表性と特性分析"""
    
    config = load_config()
    api_key = config.get('eikon_api_key')
    
    if not api_key:
        print("エラー: EIKON APIキーが設定されていません")
        return
    
    try:
        ek.set_app_key(api_key)
        print("EIKON API接続成功")
    except Exception as e:
        print(f"EIKON API接続エラー: {e}")
        return
    
    # 成功したRICから代表的なものを選択（前回テスト結果ベース）
    key_rics = {
        "SMM Yangshan港プレミアム": {
            "ric": "SMM-CUYP-CN",
            "market_focus": "中国輸入港（Yangshan）の実際の取引プレミアム",
            "liquidity_type": "実取引ベース",
            "industry_usage": "中国輸入業者の実際コスト指標"
        },
        "SHMET CIFプレミアム": {
            "ric": "CU-BPCIF-SHMET", 
            "market_focus": "上海金属交易所CIF（運賃保険込み）プレミアム",
            "liquidity_type": "交易所公式価格",
            "industry_usage": "中国国内標準価格指標"
        },
        "SHMET保税倉庫プレミアム": {
            "ric": "CU-BMPBW-SHMET",
            "market_focus": "保税倉庫在庫の現物プレミアム",
            "liquidity_type": "在庫連動型",
            "industry_usage": "現物在庫評価・取引指標"
        },
        "SHMET 1号銅プレミアム": {
            "ric": "CU1-PREM-SHMET",
            "market_focus": "高品位1号銅の品質プレミアム",
            "liquidity_type": "品質差別化価格",
            "industry_usage": "高品質銅需要セクター指標"
        },
        "SMM一般プレミアム": {
            "ric": "SMM-CU-PND",
            "market_focus": "SMM総合市場プレミアム/ディスカウント",
            "liquidity_type": "市場調査ベース",
            "industry_usage": "業界全体動向把握"
        }
    }
    
    print("=" * 80)
    print("上海銅プレミアム市場代表性・特性分析")
    print("=" * 80)
    
    analysis_results = {}
    
    for name, info in key_rics.items():
        ric = info["ric"]
        print(f"\n【{name}】")
        print(f"RIC: {ric}")
        print(f"市場焦点: {info['market_focus']}")
        print(f"流動性タイプ: {info['liquidity_type']}")
        print(f"業界用途: {info['industry_usage']}")
        
        try:
            # 過去30日間の詳細データ取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            ts_data = ek.get_timeseries(
                ric,
                fields=['CLOSE', 'HIGH', 'LOW', 'VOLUME'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if ts_data is not None and not ts_data.empty:
                # 基本統計
                close_data = ts_data['CLOSE'].dropna()
                if len(close_data) > 0:
                    mean_premium = close_data.mean()
                    std_premium = close_data.std()
                    min_premium = close_data.min()
                    max_premium = close_data.max()
                    data_points = len(close_data)
                    
                    print(f"\n統計情報（過去30日、{data_points}データポイント）:")
                    print(f"  平均プレミアム: {mean_premium:.2f} USD/MT")
                    print(f"  標準偏差: {std_premium:.2f} USD/MT")
                    print(f"  レンジ: {min_premium:.2f} - {max_premium:.2f} USD/MT")
                    print(f"  変動係数: {(std_premium/mean_premium)*100:.1f}%")
                    
                    # 安定性評価
                    cv = (std_premium/mean_premium)*100
                    if cv < 10:
                        stability = "非常に安定"
                    elif cv < 20:
                        stability = "安定"
                    elif cv < 35:
                        stability = "中程度の変動"
                    else:
                        stability = "高変動"
                    
                    print(f"  安定性評価: {stability}")
                    
                    # トレンド分析
                    if len(close_data) >= 10:
                        recent_10d = close_data.tail(10).mean()
                        older_10d = close_data.head(10).mean()
                        trend_change = recent_10d - older_10d
                        
                        if abs(trend_change) < std_premium * 0.5:
                            trend_direction = "横ばい"
                        elif trend_change > 0:
                            trend_direction = f"上昇 (+{trend_change:.2f})"
                        else:
                            trend_direction = f"下降 ({trend_change:.2f})"
                            
                        print(f"  30日トレンド: {trend_direction}")
                    
                    # 市場代表性スコア計算
                    # 1. データ可用性 (最大25点)
                    data_score = min(data_points / 30 * 25, 25)
                    
                    # 2. 安定性 (最大25点) - 低CV = 高スコア
                    stability_score = max(25 - cv, 0)
                    
                    # 3. 価格レベル妥当性 (最大25点) - 20-100 USD/MTを妥当範囲とする
                    if 20 <= mean_premium <= 100:
                        price_score = 25
                    elif 10 <= mean_premium <= 150:
                        price_score = 15
                    else:
                        price_score = 5
                    
                    # 4. 業界重要度 (最大25点) - 主観的評価
                    importance_scores = {
                        "SMM Yangshan港プレミアム": 25,  # 実取引ベース
                        "SHMET CIFプレミアム": 23,      # 交易所公式
                        "SHMET保税倉庫プレミアム": 20,   # 在庫関連
                        "SHMET 1号銅プレミアム": 18,    # 品質プレミアム
                        "SMM一般プレミアム": 15         # 総合指標
                    }
                    importance_score = importance_scores.get(name, 10)
                    
                    total_score = data_score + stability_score + price_score + importance_score
                    
                    print(f"\n市場代表性スコア:")
                    print(f"  データ可用性: {data_score:.1f}/25")
                    print(f"  安定性: {stability_score:.1f}/25") 
                    print(f"  価格妥当性: {price_score:.1f}/25")
                    print(f"  業界重要度: {importance_score:.1f}/25")
                    print(f"  総合スコア: {total_score:.1f}/100")
                    
                    # 実用性評価
                    if total_score >= 80:
                        recommendation = "強く推奨"
                    elif total_score >= 65:
                        recommendation = "推奨"
                    elif total_score >= 50:
                        recommendation = "条件付き推奨"
                    else:
                        recommendation = "非推奨"
                    
                    print(f"  実用性評価: {recommendation}")
                    
                    analysis_results[name] = {
                        'ric': ric,
                        'mean_premium': mean_premium,
                        'std_premium': std_premium,
                        'cv': cv,
                        'stability': stability,
                        'data_points': data_points,
                        'total_score': total_score,
                        'recommendation': recommendation,
                        'market_focus': info['market_focus'],
                        'industry_usage': info['industry_usage']
                    }
                    
                else:
                    print("  ✗ 有効なプレミアムデータなし")
            else:
                print("  ✗ 時系列データ取得失敗")
                
        except Exception as e:
            print(f"  ✗ 分析エラー: {e}")
    
    # 総合ランキング
    if analysis_results:
        print("\n" + "=" * 80)
        print("総合評価ランキング")
        print("=" * 80)
        
        # スコア順にソート
        ranked_results = sorted(analysis_results.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        print(f"\n🏆 推奨上海銅プレミアムRICランキング:")
        for i, (name, data) in enumerate(ranked_results, 1):
            print(f"\n{i}. {name}")
            print(f"   RIC: {data['ric']}")
            print(f"   平均プレミアム: {data['mean_premium']:.2f} ±{data['std_premium']:.2f} USD/MT")
            print(f"   安定性: {data['stability']} (CV: {data['cv']:.1f}%)")
            print(f"   総合スコア: {data['total_score']:.1f}/100")
            print(f"   評価: {data['recommendation']}")
            print(f"   用途: {data['industry_usage']}")
        
        # トップ推奨の詳細解説
        if ranked_results:
            top_choice = ranked_results[0]
            print(f"\n" + "=" * 80)
            print("最優秀選択肢詳細")
            print("=" * 80)
            print(f"\n推奨RIC: {top_choice[1]['ric']}")
            print(f"名称: {top_choice[0]}")
            print(f"\n選定理由:")
            print(f"• 市場焦点: {top_choice[1]['market_focus']}")
            print(f"• 実用性: {top_choice[1]['industry_usage']}")
            print(f"• データ品質: {top_choice[1]['data_points']}日分の安定データ")
            print(f"• 価格安定性: {top_choice[1]['stability']}（変動係数{top_choice[1]['cv']:.1f}%）")
            print(f"• 総合評価: {top_choice[1]['total_score']:.1f}/100点")
    
    return analysis_results

if __name__ == "__main__":
    try:
        results = analyze_market_characteristics()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)