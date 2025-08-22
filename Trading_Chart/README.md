# LME Copper Trading System

AIを活用したLME銅のチャートパターン認識とトレーディングシグナル生成システムです。

## 機能概要

### 1. チャート分析
- 日次OHLCVデータの可視化
- テクニカル指標の表示（移動平均、RSI、MACD、ボリンジャーバンド）
- サポート/レジスタンスレベルの自動検出

### 2. パターン認識
- **トレンドパターン**: 移動平均クロスオーバー
- **モメンタムパターン**: RSIダイバージェンス
- **価格アクション**: サポート/レジスタンスブレイクアウト
- **ローソク足パターン**: ハンマー、流れ星、包み足

### 3. バックテスト機能
- 各種パターンの過去パフォーマンス検証
- 勝率、リターン、シャープレシオなどの評価指標
- パターン組み合わせの最適化機能

### 4. リアルタイムシグナル
- 最新のチャートパターンに基づく売買シグナル
- 信頼度スコア付きのアラート

## セットアップ

### 前提条件
- Python 3.8以上
- SQL Server（LME銅データが格納されているもの）
- Windows OS（PyQt5のため）

### インストール手順

1. リポジトリのクローン
```bash
git clone [repository_url]
cd Trading_Chart
```

2. 仮想環境の作成（推奨）
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

4. TA-Libのインストール（Windows）
   - [TA-Lib公式サイト](https://www.ta-lib.org/)からWindows用バイナリをダウンロード
   - または、[非公式Wheel](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)からインストール

5. 環境設定
   - `.env.example`を`.env`にコピー
   - SQL Server接続情報を設定

## 使用方法

### アプリケーションの起動
```bash
python main.py
```

### 基本的な操作フロー

1. **データ読み込み**
   - アプリケーション起動時に自動的にSQL Serverから過去3年分のデータを読み込み

2. **チャート分析**
   - "Chart Analysis"タブでテクニカル指標を選択
   - "Update Chart"でチャートを更新

3. **パターン分析**
   - "Trading Signals"タブで"Analyze Current Patterns"をクリック
   - 最新の売買シグナルを確認

4. **バックテスト実行**
   - "Backtesting"タブでパターンとポジションサイズを選択
   - "Run Backtest"で過去データでの検証
   - "Optimize Patterns"で最適なパターン組み合わせを探索

## データベース構成

SQL ServerのLME_Copper_Dailyテーブルに以下のカラムが必要：
- Date (datetime)
- Open (float)
- High (float)
- Low (float)
- Close (float)
- Volume (float)

## プロジェクト構造

```
Trading_Chart/
├── src/
│   ├── data/          # データ取得モジュール
│   ├── analysis/      # テクニカル分析・パターン認識
│   ├── backtest/      # バックテストエンジン
│   ├── ui/            # GUIコンポーネント
│   └── utils/         # ユーティリティ関数
├── config/            # 設定ファイル
├── tests/             # テストコード
├── docs/              # ドキュメント
├── main.py            # エントリーポイント
├── requirements.txt   # 依存関係
└── README.md          # このファイル
```

## 今後の拡張予定

### フェーズ2（機械学習強化）
- CNNによるチャートパターン認識
- LSTMによる価格予測
- 強化学習による最適化

### フェーズ3（リアルタイム対応）
- ストリーミングデータ対応
- リアルタイムアラート機能
- 自動取引機能

## トラブルシューティング

### SQL Server接続エラー
- Windows認証が有効か確認
- ファイアウォール設定を確認
- SQL Serverサービスが起動しているか確認

### TA-Libインストールエラー
- Visual C++ Redistributableがインストールされているか確認
- 適切なPythonバージョン用のwheelファイルを使用

## ライセンス

このプロジェクトは内部使用のみを目的としています。