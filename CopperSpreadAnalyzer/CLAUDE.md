# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 開発コマンド

### Copper Spread Analyzerの実行
```bash
# メインのスプレッド分析システム（分単位データ・日本時間基準）
python copper_spread_jst_minute.py

# 過去のシステム（参考用）
python copper_spread_london_daily.py      # ロンドン時間・日次データ版
python copper_spread_london_minute.py     # ロンドン時間・分単位版
```

### テスト実行
```bash
# 個別スプレッドテスト
python test_single_ric.py                 # 単一RICの取得テスト
python test_spread_data.py                # スプレッドデータ取得テスト

# 全スプレッド組み合わせテスト
python test_all_spreads.py                # 基本的な全スプレッドテスト
python test_all_spreads_24m.py            # 24ヶ月分限月テスト
python test_all_spreads_consolidated.py   # 統合版テスト

# データ検証テスト
python test_tick_data.py                  # ティックデータ検証
python test_historical_range.py           # 過去データ範囲テスト
python test_valid_intervals.py            # 有効インターバル確認
python test_filtered_summary.py           # サマリーフィルタリングテスト
```

### 環境設定
```bash
# 仮想環境作成と有効化
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate     # Windows

# 依存関係インストール（親ディレクトリから）
pip install -r ../requirements.txt

# EIKON API接続確認
python -c "import eikon as ek; ek.set_app_key('test'); print('EIKON API available')"
```

### ログとデータ確認
```bash
# 最新ログ確認
tail -f logs/copper_spread_jst_minute.log

# 出力データ確認
ls -la output/
cat output/copper_spread_summary_minute_jst_$(date +%Y-%m-%d).csv
```

## アーキテクチャ概要

### Copper Spread Analyzerシステム設計
LME（London Metal Exchange）銅先物スプレッド取引の包括的データ分析システム：

1. **データ取得アーキテクチャ**: Refinitiv EIKON API → 分単位スプレッドデータ取得 → 日本時間フィルタリング → CSV出力
2. **スプレッド組み合わせ生成**: Cash + 3M + 25ヶ月分第3水曜限月 = 27個から2個選択（351組み合わせ）
3. **時間帯処理**: マルチデイ範囲取得 → 特定日フィルタリング（API制約対応）
4. **前日終値機能**: 各スプレッドの前営業日終値を自動取得してサマリーに追加

### 主要コンポーネント

#### copper_spread_jst_minute.py（メインシステム）
- **スプレッド生成**: 動的な25ヶ月限月コード生成（第3水曜日ベース）
- **データ取得**: マルチデイ範囲指定による分単位データ取得
- **日本時間処理**: UTC → JST変換なしのシンプル日付フィルタリング
- **前日終値取得**: `get_previous_close_price()`関数による前営業日終値の自動取得
- **サマリー生成**: 取引があったスプレッドのみの整理されたサマリー

#### 限月コードシステム
```python
month_codes = {
    1: 'F', 2: 'G', 3: 'H', 4: 'J', 5: 'K', 6: 'M',
    7: 'N', 8: 'Q', 9: 'U', 10: 'V', 11: 'X', 12: 'Z'
}
```
- **RIC命名規則**: `CMCU{near_leg}-{far_leg}` (例: CMCU0-N25, CMCU3-V25)
- **基本インストゥルメント**: Cash(0), 3Month(3), + 25ヶ月分第3水曜限月

#### データフロー
1. **限月生成**: 25ヶ月先までの第3水曜限月コード自動生成
2. **組み合わせ生成**: 27個インストゥルメントから351個のスプレッド組み合わせ作成
3. **API呼び出し**: 各スプレッドに対してマルチデイ範囲で分単位データ取得
4. **日付フィルタリング**: 指定日の取引データのみを抽出
5. **前日終値取得**: 各アクティブスプレッドの前営業日終値を取得
6. **出力生成**: 取引明細CSVとサマリーCSVの2ファイル出力

### 重要な技術的制約と対処法

#### EIKON API分単位データ制約
- **単日指定問題**: `start_date=end_date`では分単位データが取得できない
- **解決法**: マルチデイ範囲（例：2025-06-13〜2025-06-17）で取得後、クライアント側で日付フィルタリング
- **実装場所**: `get_spread_data_minute()`関数の204-214行目

#### 営業日計算
```python
# 前営業日計算（土日除外）
while target_date.weekday() >= 5:  # 土曜(5)、日曜(6)
    target_date -= timedelta(days=1)
```

#### スプレッドデータの特性
- **流動性の偏在**: 351組み合わせのうち実際に取引があるのは通常30-40個程度
- **サマリー最適化**: `status == 'success_with_trades'`のみをサマリーに含める
- **フィールド整理**: `far_leg`から"Third_Wed"プレフィックスを削除

### 出力ファイル構造

#### 取引明細ファイル
`copper_spread_trades_minute_jst_YYYY-MM-DD.csv`
- 各取引の分単位記録（spread_ric, near_leg, far_leg, trade_datetime, volume, price等）

#### サマリーファイル
`copper_spread_summary_minute_jst_YYYY-MM-DD.csv`  
- 取引があったスプレッドの日次サマリー（取引件数、総出来高、価格レンジ、前日終値等）
- **重要**: 前日終値（`previous_close`）フィールドを含む

### テストファイル分類

#### 基本機能テスト
- `test_single_ric.py`: 単一RICの取得可能性確認
- `test_spread_data.py`: スプレッドデータ基本取得テスト

#### 包括的テスト
- `test_all_spreads_24m.py`: 24ヶ月分全組み合わせテスト（最も包括的）
- `test_all_spreads_consolidated.py`: 統合システムテスト

#### データ検証テスト
- `test_historical_range.py`: 過去データ範囲の検証
- `test_valid_intervals.py`: 有効な時間間隔の確認
- `test_filtered_summary.py`: サマリーフィルタリング機能テスト

### 設定ファイル依存関係
- **親ディレクトリのconfig.json**: EIKON APIキーと基本設定
- **相対パス処理**: `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`で親ディレクトリアクセス

### パフォーマンス特性
- **実行時間**: 全351組み合わせで約15-20分（API制限による）
- **API制限対策**: 各リクエスト間に0.05秒の待機時間
- **メモリ使用量**: 分単位データのため数MB〜数十MB程度

### エラーハンドリング
- **データなしエラー**: "No data available for the requested date range" → ログ記録して継続
- **無効RICエラー**: "Invalid RIC" → 将来の限月で発生、ログ記録して継続  
- **前日終値取得失敗**: None値を設定してサマリー生成継続

## 重要事項

### データ取得の時間制約
- **LME取引時間**: 日本時間早朝〜夕方がメイン取引時間
- **最適取得日**: 前営業日のデータ取得が基本
- **週末処理**: 月曜実行時は金曜日データを自動取得

### RIC命名パターンの理解
- **Cash**: CMCU0-xxx（現物vs先物）
- **3Month**: CMCU3-xxx（3ヶ月vs他期間）  
- **限月vs限月**: CMCUxxx-yyy（期間構造スプレッド）

### API利用上の注意
- **config.json**のAPIキーは実際の値が設定済み
- **同時リクエスト制限**: 0.05秒間隔での順次処理
- **データ権限**: 一部の将来限月でアクセス制限の可能性

### 前日終値機能の活用
- **価格比較**: 当日取引価格と前日終値の比較分析が可能
- **トレンド分析**: 前日からの価格変動パターン把握
- **リスク管理**: 前日比での価格変動率計算