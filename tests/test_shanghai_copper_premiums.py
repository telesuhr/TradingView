#!/usr/bin/env python3
"""
上海銅プレミアムRIC包括テスト - データ可用性と市場代表性評価
"""

import sys
import json
import eikon as ek
import pandas as pd
from datetime import datetime, timedelta

def load_config():
    """設定ファイル読み込み"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイル読み込みエラー: {e}")
        return {}

def test_shanghai_copper_premiums():
    """上海銅プレミアムRIC包括テスト"""
    
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
    
    # 提供されたRICリスト（スポット価格のみ - 先物は除外）
    shanghai_copper_rics = {
        # SMM系 (Shanghai Metals Market)
        "SMM Yangshan Copper Premiums (Under Warrants)": {
            "ric": "SMM-CUYP-CN",
            "source": "SHANGHAI METALS MARKET",
            "type": "Yangshan港プレミアム",
            "category": "SMM"
        },
        "SMM 1 Copper Premiums/Discounts": {
            "ric": "SMM-CU-PND", 
            "source": "SHANGHAI METALS MARKET",
            "type": "一般プレミアム/ディスカウント",
            "category": "SMM"
        },
        
        # SHMET系 (Shanghai Metal Exchange)
        "SHMET CIF Premium": {
            "ric": "CU-BPCIF-SHMET",
            "source": "Shanghai Metal Exchange", 
            "type": "CIFプレミアム",
            "category": "SHMET"
        },
        "SHMET Bonded Warehouse Premium": {
            "ric": "CU-BMPBW-SHMET",
            "source": "Shanghai Metal Exchange",
            "type": "保税倉庫プレミアム", 
            "category": "SHMET"
        },
        "SHMET Copper SXEW B/L Premium": {
            "ric": "CU-SXBL-SHMET",
            "source": "Shanghai Metal Exchange",
            "type": "SXEW B/Lプレミアム",
            "category": "SHMET"
        },
        "SHMET Copper 1# Premium": {
            "ric": "CU1-PREM-SHMET",
            "source": "Shanghai Metal Exchange",
            "type": "1号銅プレミアム",
            "category": "SHMET"
        },
        "SHMET Copper 1# SXEW Premium": {
            "ric": "CU1-SXEW-SHMET",
            "source": "Shanghai Metal Exchange",
            "type": "1号銅SXEWプレミアム",
            "category": "SHMET"
        },
        "SHMET Copper Cathode #1 Premium": {
            "ric": "CU1-CATH-SHMET",
            "source": "Shanghai Metal Exchange",
            "type": "カソード1号プレミアム",
            "category": "SHMET"
        },
        "SHMET Copper ER Bonded Premium": {
            "ric": "CU-ERBP-SHMET",
            "source": "Shanghai Metal Exchange",
            "type": "ER保税プレミアム",
            "category": "SHMET"
        },
        "SHMET Copper 1# Flat Premium": {
            "ric": "CU1-FLAT-SHMET",
            "source": "Shanghai Metal Exchange",
            "type": "1号フラット銅プレミアム",
            "category": "SHMET"
        },
        "SHMET Copper ER B/L Premium": {
            "ric": "CE-ERBL-SHMET",
            "source": "Shanghai Metal Exchange",
            "type": "ER B/Lプレミアム",
            "category": "SHMET"
        },
        "SHMET Copper SXEW Bonded Premium": {
            "ric": "CU-SXBP-SHMET", 
            "source": "Shanghai Metal Exchange",
            "type": "SXEW保税プレミアム",
            "category": "SHMET"
        }
    }
    
    print("=" * 80)
    print("上海銅プレミアムRIC包括テスト - データ可用性と流動性評価")
    print("=" * 80)
    
    results = {}
    successful_rics = []
    failed_rics = []
    
    for name, info in shanghai_copper_rics.items():
        ric = info["ric"]
        category = info["category"]
        type_desc = info["type"]
        
        print(f"\n【{name}】")
        print(f"  RIC: {ric}")
        print(f"  分類: {category}")
        print(f"  種類: {type_desc}")
        
        try:
            # 基本データ取得テスト
            fields = ['CF_LAST', 'CF_DATE', 'CF_NAME', 'CF_HIGH', 'CF_LOW', 'CF_CLOSE']
            data, err = ek.get_data(ric, fields)
            
            if data is not None and not data.empty:
                row = data.iloc[0]
                last_value = row.get('CF_LAST')
                last_date = row.get('CF_DATE')
                name_field = row.get('CF_NAME')
                high_value = row.get('CF_HIGH')
                low_value = row.get('CF_LOW')
                close_value = row.get('CF_CLOSE')
                
                if pd.notna(last_value) and last_value is not None:
                    print(f"  ✓ 最新値: {last_value:.2f} USD/MT")
                    print(f"  ✓ 日付: {last_date}")
                    if pd.notna(name_field):
                        print(f"  ✓ 名称: {name_field}")
                    
                    # 価格レンジ情報
                    price_range_info = []
                    if pd.notna(high_value):
                        price_range_info.append(f"高値: {high_value:.2f}")
                    if pd.notna(low_value):
                        price_range_info.append(f"安値: {low_value:.2f}")
                    if pd.notna(close_value):
                        price_range_info.append(f"終値: {close_value:.2f}")
                    
                    if price_range_info:
                        print(f"  ✓ 価格情報: {', '.join(price_range_info)}")
                    
                    # 時系列データテスト（過去7日）
                    try:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=7)
                        
                        ts_data = ek.get_timeseries(
                            ric,
                            fields=['CLOSE'],
                            start_date=start_date.strftime('%Y-%m-%d'),
                            end_date=end_date.strftime('%Y-%m-%d')
                        )
                        
                        if ts_data is not None and not ts_data.empty:
                            data_points = len(ts_data.dropna())
                            if data_points > 0:
                                recent_avg = ts_data['CLOSE'].dropna().mean()
                                recent_std = ts_data['CLOSE'].dropna().std()
                                print(f"  ✓ 時系列データ: {data_points}日分")
                                print(f"  ✓ 7日平均: {recent_avg:.2f} USD/MT")
                                if pd.notna(recent_std):
                                    print(f"  ✓ 7日標準偏差: {recent_std:.2f}")
                                
                                # データ品質評価
                                if data_points >= 5:
                                    data_quality = "高品質"
                                elif data_points >= 3:
                                    data_quality = "中品質"
                                else:
                                    data_quality = "低品質"
                                
                                print(f"  ✓ データ品質: {data_quality}")
                                
                                # 結果記録
                                results[name] = {
                                    'ric': ric,
                                    'category': category,
                                    'type': type_desc,
                                    'last_value': last_value,
                                    'last_date': str(last_date),
                                    'data_points': data_points,
                                    'avg_7d': recent_avg,
                                    'std_7d': recent_std if pd.notna(recent_std) else 0,
                                    'data_quality': data_quality,
                                    'status': 'success'
                                }
                                successful_rics.append(name)
                                print(f"  → 評価: 成功")
                            else:
                                print(f"  ✗ 時系列データなし")
                                failed_rics.append(name)
                        else:
                            print(f"  ✗ 時系列データ取得失敗")
                            failed_rics.append(name)
                            
                    except Exception as ts_error:
                        print(f"  ✗ 時系列データエラー: {ts_error}")
                        failed_rics.append(name)
                        
                else:
                    print(f"  ✗ 有効な価格データなし")
                    failed_rics.append(name)
            else:
                print(f"  ✗ データ取得失敗")
                failed_rics.append(name)
            
            if err:
                print(f"  警告: {err}")
                
        except Exception as e:
            print(f"  ✗ RICエラー: {e}")
            failed_rics.append(name)
    
    # 結果分析とランキング
    print("\n" + "=" * 80)
    print("データ可用性・品質分析結果")
    print("=" * 80)
    
    if successful_rics:
        print(f"\n✓ 有効RIC: {len(successful_rics)}/{len(shanghai_copper_rics)}")
        
        # カテゴリ別成功率
        category_stats = {}
        for name in successful_rics:
            if name in results:
                cat = results[name]['category']
                if cat not in category_stats:
                    category_stats[cat] = 0
                category_stats[cat] += 1
        
        print(f"\nカテゴリ別成功率:")
        for cat, count in category_stats.items():
            total_in_cat = sum(1 for info in shanghai_copper_rics.values() if info['category'] == cat)
            success_rate = (count / total_in_cat) * 100
            print(f"  {cat}: {count}/{total_in_cat} ({success_rate:.1f}%)")
        
        # データ品質ランキング
        quality_ranking = []
        for name, data in results.items():
            if data['status'] == 'success':
                # スコア計算: データポイント数 + 品質ボーナス + 流動性指標
                score = data['data_points'] * 2
                if data['data_quality'] == '高品質':
                    score += 10
                elif data['data_quality'] == '中品質':
                    score += 5
                
                # 標準偏差（ボラティリティ）を流動性指標として使用
                if data['std_7d'] > 0:
                    score += min(data['std_7d'], 5)  # 最大5ポイント
                
                quality_ranking.append((name, data, score))
        
        # スコア順にソート
        quality_ranking.sort(key=lambda x: x[2], reverse=True)
        
        print(f"\n🏆 推奨RICランキング（データ品質・流動性ベース）:")
        for i, (name, data, score) in enumerate(quality_ranking[:5], 1):
            print(f"  {i}. {name}")
            print(f"     RIC: {data['ric']}")
            print(f"     最新値: {data['last_value']:.2f} USD/MT")
            print(f"     データ品質: {data['data_quality']} ({data['data_points']}日)")
            print(f"     7日平均: {data['avg_7d']:.2f} ±{data['std_7d']:.2f}")
            print(f"     総合スコア: {score:.1f}")
            print()
    
    if failed_rics:
        print(f"\n✗ 無効RIC: {len(failed_rics)}")
        for name in failed_rics:
            ric = shanghai_copper_rics[name]['ric']
            print(f"  - {name} ({ric})")
    
    return results, successful_rics, failed_rics

if __name__ == "__main__":
    try:
        results, successful, failed = test_shanghai_copper_premiums()
        print(f"\n実行完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"スクリプト実行エラー: {e}")
        sys.exit(1)