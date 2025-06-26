# LME金属マーケットレポート自動化システム

London Metal Exchange（LME）主要6金属の日次マーケットデータを自動取得し、Web版Claude用の完結型レポートファイルを生成するPythonシステムです。

## 概要

本システムは、Refinitiv EIKON Data APIを使用してLME主要6金属（銅、アルミ、亜鉛、鉛、ニッケル、錫）の以下のデータを自動取得します：

- **価格データ**: 前日終値、変動率、キャッシュプレミアム等
- **在庫データ**: LME、COMEX、SHFE各取引所の在庫状況
- **取引量データ**: 出来高、建玉データ
- **マクロ経済データ**: USD指数、債券利回り、原油価格等
- **ニュースデータ**: 各金属関連の最新ニュース

## システム要件

### 必須要件
- Python 3.7以上
- Refinitiv EIKON Data API ライセンス
- インターネット接続

### 推奨環境
- Windows 10/11 または Linux/macOS
- メモリ 4GB以上
- ディスク容量 1GB以上

## インストール手順

### 1. リポジトリのクローン
```bash
git clone <repository_url>
cd DailyReporting
```

### 2. 仮想環境の作成
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

### 4. 設定ファイルの編集
`config.json`を開き、以下を設定してください：

```json
{
  "eikon_api_key": "YOUR_ACTUAL_EIKON_API_KEY"
}
```

### 5. 環境変数の設定（オプション）
```bash
# .envファイルを作成
cp .env.example .env
# .envファイルを編集してAPIキー等を設定
```

## 使用方法

### 手動実行

#### Windows
```cmd
run_report.bat
```

#### Linux/macOS
```bash
./run_report.sh
```

#### Python直接実行
```bash
python lme_daily_report.py
```

### 自動実行の設定

#### Windows タスクスケジューラー
1. タスクスケジューラーを開く
2. 「基本タスクの作成」を選択
3. 以下を設定：
   - 名前: "LME Daily Report"
   - トリガー: 毎日 午前8:00
   - アクション: プログラムの開始
   - プログラム: `run_report.bat`の完全パス

#### Linux/macOS cron
```bash
# crontabを編集
crontab -e

# 毎日午前8:00に実行
0 8 * * * /path/to/DailyReporting/run_report.sh
```

## 出力ファイル

### 生成されるファイル
- `output/LME_Daily_Report_Input_YYYYMMDD.txt`: Claude用レポートファイル
- `logs/lme_report_YYYYMMDD.log`: 実行ログ

### ファイル構造
```
LME_Daily_Report_Input_20250610.txt
├── Claude用プロンプト部分
├── レポート要件
├── 市場データ
│   ├── 価格動向
│   ├── 在庫状況
│   ├── 取引量
│   ├── マクロ環境
│   └── 関連ニュース
└── 分析指示
```

## 設定ファイル詳細

### config.json 主要設定項目

| 項目 | 説明 | 例 |
|------|------|-----|
| `eikon_api_key` | EIKON APIキー | "YOUR_API_KEY" |
| `metals_rics` | 金属RICコード | {"Copper": "CMCU3"} |
| `output_settings` | 出力設定 | ディレクトリ、ファイル名形式 |
| `error_handling` | エラー処理設定 | リトライ回数、タイムアウト |

### 取得データの詳細

#### 価格データ
- 前日終値（3ヶ月先物）
- 当日始値、日中高値・安値
- 前日比、週次、月次、年初来変動率
- キャッシュプレミアム/ディスカウント
- バックワーデーション/コンタンゴ状況

#### 在庫データ
- **LME**: 総在庫量、Live warrant、キャンセレーション
- **COMEX**: 銅の総在庫、Registered/Eligible内訳
- **SHFE**: 全6金属の公式在庫量

#### マクロ経済データ
- USD Index（ドル指数）
- 10年米国債利回り
- 原油価格（WTI）
- 中国製造業PMI

## トラブルシューティング

### よくある問題

#### 1. API接続エラー
```
[ERROR] EIKON API初期化エラー
```
**解決方法:**
- APIキーが正しく設定されているか確認
- EIKON Desktopが起動しているか確認
- ネットワーク接続を確認

#### 2. データ取得エラー
```
[WARNING] データ取得警告
```
**解決方法:**
- 市場が開いているか確認（祝日・休場日ではないか）
- RICコードが正しいか確認
- APIの利用制限に達していないか確認

#### 3. 権限エラー
```
[ERROR] ファイル書き込みエラー
```
**解決方法:**
- `output`および`logs`ディレクトリの書き込み権限を確認
- 管理者権限で実行

### ログファイルの確認
```bash
# 最新のログを確認
tail -f logs/lme_report_$(date +%Y%m%d).log
```

## システム構成

```
DailyReporting/
├── lme_daily_report.py     # メインスクリプト
├── config.json             # 設定ファイル
├── requirements.txt        # 必要なパッケージ
├── run_report.bat         # Windows実行スクリプト
├── run_report.sh          # Linux/macOS実行スクリプト
├── .env.example           # 環境変数例
├── README.md              # このファイル
├── output/                # 出力ディレクトリ
├── logs/                  # ログディレクトリ
└── venv/                  # 仮想環境（作成後）
```

## 拡張機能

### カスタマイゼーション
- `config.json`で取得データの調整が可能
- 新しい金属や経済指標の追加が容易
- レポート形式のカスタマイズ対応

### 将来の拡張予定
- リアルタイムアラート機能
- データベース連携
- Webダッシュボード
- 機械学習による価格予測

## ライセンス

このソフトウェアは商用利用可能です。Refinitiv EIKON Data APIの利用規約に従ってご使用ください。

## サポート

問題や質問がある場合は、以下の方法でサポートを受けられます：

1. ログファイルを確認
2. 設定ファイルの確認
3. APIキーとネットワーク接続の確認

## 変更履歴

### v1.0.0 (2025-06-10)
- 初期リリース
- LME主要6金属の価格・在庫・取引量データ取得機能
- Claude用レポートファイル自動生成機能
- Windows/Linux/macOS対応

---

**Author:** Claude Code  
**Created:** 2025-06-10  
**Version:** 1.0.0
