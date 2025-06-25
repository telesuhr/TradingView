# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## 開発コマンド

### LME日次レポートシステム
```bash
# メインレポート生成システム
python lme_daily_report.py

# クロスプラットフォーム実行
./run_report.sh          # Linux/macOS
run_report.bat           # Windows
```

### 銅スプレッドアナライザーシステム
```bash
# 対話型スプレッド分析システム（推奨）
python CopperSpreadAnalyzer/copper_spread_jst_minute.py

# 非対話型バッチ処理
python CopperSpreadAnalyzer/run_historical_batch.py --date 2025-06-18
python CopperSpreadAnalyzer/run_historical_batch.py --recent 5

# 月次レポート生成
python CopperSpreadAnalyzer/generate_monthly_report.py
```

### 環境設定
```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 依存関係インストール
pip install -r requirements.txt

# EIKON API接続確認
python -c "import eikon as ek; ek.set_app_key('test'); print('EIKON API available')"
```

### テスト実行
```bash
# LME日次レポートテスト
python -c "from lme_daily_report import LMEReportGenerator; gen = LMEReportGenerator(); print(gen.get_price_data())"

# 銅スプレッドアナライザーテスト
cd CopperSpreadAnalyzer
python test_single_ric.py
python test_all_spreads_24m.py            # 最も包括的
python test_filtered_summary.py
```

### ログとデータ確認
```bash
# LMEレポートログ
tail -f logs/lme_report_$(date +%Y%m%d).log
ls -la output/LME_Daily_Report_Input_$(date +%Y%m%d).txt

# 銅スプレッドログ
tail -f CopperSpreadAnalyzer/logs/copper_spread_jst_minute.log
ls -la CopperSpreadAnalyzer/output/
```

## アーキテクチャ概要

このリポジトリには2つの主要システムが含まれており、どちらもRefinitiv EIKON APIを使用して金属市場データを取得します：

### 1. LME日次レポートシステム（ルートディレクトリ）
Claude分析用の包括的市場レポート生成システム

**設計原則：**
- **単一目的データ集約**: LME主要6金属の全市場データを1つのプロンプトファイルに統合
- **Claude最適化**: 構造化テキストファイルでClaude分析向けに設計
- **エラー耐性**: 包括的フォールバック機構とリトライロジック
- **無人実行**: タスクスケジューラーでの日次自動実行向け

**主要コンポーネント：**
- `LMEReportGenerator`クラス: 中央制御システム
- データ収集メソッド: 価格、在庫、取引量、マクロ、ニュース、フォワードカーブ
- RIC管理: 広範なRICマッピングと代替RIC機構
- レポート出力: `output/LME_Daily_Report_Input_YYYYMMDD.txt`

### 2. 銅スプレッドアナライザーシステム（CopperSpreadAnalyzerディレクトリ）
LME銅先物スプレッド取引の専門分析システム

**設計原則：**
- **専門特化**: 銅先物スプレッド351組み合わせの網羅的分析
- **高頻度データ**: 分単位取引データの詳細分析
- **対話型UI**: ユーザーフレンドリーな日付選択インターフェース
- **期間構造分析**: 前日終値、最終価格、価格変動パターン分析

**主要コンポーネント：**
- 対話型システム: `copper_spread_jst_minute.py`（メイン）
- バッチ処理: `run_historical_batch.py`
- レポート生成: `generate_monthly_report.py`
- 出力ファイル: 日次取引明細とサマリーCSV

## システム間の相互関係

### 共通基盤
- **EIKON API**: 両システムともRefinitiv EIKON Data APIを使用
- **設定管理**: 共通の`config.json`でAPIキーを管理
- **営業日計算**: 土日除外の営業日ベース日付処理
- **エラーハンドリング**: API制限とデータ取得失敗への対応

### 異なる焦点
- **LME日次レポート**: 広範な市場データ → Claude分析 → 意思決定支援
- **銅スプレッドアナライザー**: 詳細取引データ → CSV分析 → トレーディング支援

## 重要な技術的制約

### EIKON API制約と対処法
- **分単位データ制約**: 単日指定では取得不可 → マルチデイ範囲取得後フィルタリング
- **API制限**: Rate limiting対応 → 0.05-2秒間隔での順次処理
- **RIC権限**: 一部先物限月でアクセス制限 → 代替RIC機構とエラー継続処理

### データ取得方法論
- **get_timeseries() vs get_data()**: フォワードカーブ等の正確な過去価格には`get_timeseries()`を使用
- **営業日計算**: `weekday() >= 5`で土日除外の正確な営業日ベース計算
- **pandas NA値処理**: `pd.isna()`による適切なnullチェックが必須

## 設定ファイル構造

### config.json（共通設定）
```json
{
  "eikon_api_key": "YOUR_ACTUAL_API_KEY",
  "metals_rics": {
    "Copper": "CMCU3",
    "Aluminium": "CMAL3"
  },
  "forward_curve_rics": {},
  "equity_indices": {},
  "usdjpy_swap_rates": {},
  "news_settings": {
    "enable_news_collection": true
  }
}
```

**重要項目：**
- `metals_rics`: メイン金属RIC（3ヶ月先物）
- `forward_curve_rics`: 従来固定期間RIC（現在未使用、動的生成に移行）
- `equity_indices`: 現物・先物混合設定（権限最適化済み）
- `news_settings`: ニュース取得の有効/無効切替

## パフォーマンス特性

### LME日次レポート
- **実行時間**: 通常2-3分、フォワードカーブ取得が主要時間要因
- **ボトルネック**: ニュース取得（API制限）、24ヶ月×6金属の時系列データ
- **最適化**: `enable_news_collection: false`で約2-3分に短縮

### 銅スプレッドアナライザー
- **実行時間**: 全351組み合わせで約15-20分（API制限による）
- **メモリ使用**: 分単位データで数MB〜数十MB
- **流動性**: 351組み合わせ中30-40個程度で実際取引あり

## エラー復旧手順

### 共通問題
1. **API接続エラー**: APIキー確認、EIKON Desktop起動確認
2. **datetime64エラー**: 修正済み、文字列形式日付使用
3. **API制限エラー**: `enable_news_collection: false`設定
4. **RIC無効エラー**: ログ確認後、代替RIC検索

### システム固有問題
- **LMEレポート**: フォールバックデータで継続、`config.json`調整
- **銅スプレッド**: 前日終値取得失敗時はNone値設定で継続

## 出力ファイル構造

### LME日次レポート
```
output/LME_Daily_Report_Input_YYYYMMDD.txt
├── Claude用プロンプト部分
├── 市場データ（価格、在庫、取引量、マクロ、ニュース）
└── 分析指示
```

### 銅スプレッドアナライザー
```
CopperSpreadAnalyzer/output/
├── copper_spread_trades_minute_jst_YYYY-MM-DD.csv      # 分単位取引明細
├── copper_spread_summary_minute_jst_YYYY-MM-DD.csv     # 日次サマリー
├── copper_spread_monthly_report_START_to_END.csv       # 月次集計
└── copper_spread_daily_summary_START_to_END.csv        # 日別統計
```

## 重要事項

### APIキー管理
- `config.json`のEIKON APIキーは実際の値が設定済み
- 機密情報のため、コミット時は必ず確認

### 銅スプレッド分析の活用
- **RIC命名**: `CMCU{near_leg}-{far_leg}` (例: CMCU0-N25, CMCU3-V25)
- **限月コード**: F=1月, G=2月, H=3月, J=4月, K=5月, M=6月, N=7月, Q=8月, U=9月, V=10月, X=11月, Z=12月
- **前日終値機能**: 当日取引価格と前日終値の比較分析が可能

### 営業日計算の精度
両システムとも土日を正確に除外した営業日ベース計算を実装。週末や祝日の自動処理により、月曜実行時は金曜日データを自動取得。

## 銅スプレッドアナライザーの対話型実行

メインスクリプト実行時の対話フロー：
```
==================================================
LME銅スプレッドデータ取得システム
==================================================
実行モードを選択してください:
1. 単一日付を指定
2. 期間を指定
3. 直近N営業日
4. 過去1ヶ月分（自動）
==================================================
```

各モードで適切な日付入力を求められ、ユーザーフレンドリーな方式でデータ取得が可能。