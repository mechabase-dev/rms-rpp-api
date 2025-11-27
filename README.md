# 楽天RMS RPPレポートAPI

このAPIは、楽天RMSからRPPレポートのCSVファイルを取得するためのAPIです。

## セットアップ

### 1. 依存関係のインストール

```bash
cd api
pip install -r requirements.txt
playwright install chromium
```

### 2. 環境変数の設定

`.env`ファイルを作成するか、環境変数を設定してください：

```bash
# RMS認証情報
export RMS_LOGIN_ID="your_rms_login_id"
export RMS_PASSWORD="your_rms_password"

# 楽天会員認証情報
export RAKUTEN_USER_ID="your_rakuten_user_id"
export RAKUTEN_PASSWORD="your_rakuten_password"
```

または、JSON形式で設定することもできます：

```bash
export RMS_CREDENTIALS='{"login_id": "your_rms_login_id", "password": "your_rms_password"}'
export RAKUTEN_CREDENTIALS='{"user_id": "your_rakuten_user_id", "password": "your_rakuten_password"}'
```

### 3. APIサーバーの起動

```bash
# APIディレクトリから実行
cd api
uvicorn main:app --reload
```

または、直接実行：

```bash
cd api
python main.py
```

## エンドポイント

### GET /rpp-report

指定された日付のRPPレポートCSVを取得します。

#### パラメータ

- `date` (必須): 取得するレポートの日付 (YYYY-MM-DD形式)
  - 例: `2024-01-01`

#### レスポンス

- 成功時: CSVファイル（Content-Type: text/csv）
- エラー時: JSON形式のエラーメッセージ

#### 使用例

```bash
# 2024年1月1日のレポートを取得
curl "http://localhost:8000/rpp-report?date=2024-01-01" -o rpp_report_2024-01-01.csv
```

#### エラーレスポンス

- `400 Bad Request`: 無効な日付形式
- `404 Not Found`: 指定された日付のレポートが見つからない
- `500 Internal Server Error`: サーバー内部エラー

## 注意事項

- このAPIは、楽天RMSへのログインとレポートのダウンロード処理を行うため、実行に時間がかかる場合があります。
- 環境変数から認証情報を取得するため、適切な環境変数が設定されている必要があります。
- ブラウザの自動化処理（Playwright）を使用するため、適切な環境が整っている必要があります。

