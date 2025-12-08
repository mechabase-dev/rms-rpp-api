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

# OAuth2認証設定（必須）
export SECRET_KEY="your-secret-key-change-this-in-production"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"

# OAuth2クライアント設定（Client Credentialsフロー用、n8n推奨）
export OAUTH_CLIENT_ID="n8n"
export OAUTH_CLIENT_SECRET="n8n-secret"
export OAUTH_CLIENT_SCOPE="read"

# OAuth2クライアント設定（方法2: 複数クライアント、JSON形式）
export OAUTH_CLIENTS='[{"client_id":"n8n","client_secret":"n8n-secret","scope":"read"},{"client_id":"other-app","client_secret":"other-secret","scope":"read write"}]'

# OAuth2ユーザー設定（Password Credentialsフロー用、オプション）
export OAUTH_USERNAME="admin"
export OAUTH_PASSWORD="your_password"
export OAUTH_EMAIL="admin@example.com"

# OAuth2ユーザー設定（方法2: 複数ユーザー、JSON形式）
export USERS='[{"username":"admin","password":"your_password","email":"admin@example.com"},{"username":"user1","password":"password1","email":"user1@example.com"}]'

# CORS設定（n8nなどの外部ツールからのアクセスを許可、カンマ区切り）
export CORS_ORIGINS="http://localhost:5678,https://your-n8n-domain.com"
```

または、JSON形式で設定することもできます：

```bash
export RMS_CREDENTIALS='{"login_id": "your_rms_login_id", "password": "your_rms_password"}'
export RAKUTEN_CREDENTIALS='{"user_id": "your_rakuten_user_id", "password": "your_rakuten_password"}'
```

**注意**: `SECRET_KEY`は本番環境では必ず強力なランダム文字列に変更してください。

### 3. APIサーバーの起動

```bash
# 方法1: uvicornを使用（推奨、ホットリロード対応）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

または、直接実行：

```bash
python main.py
```

サーバーが起動すると、以下のURLでアクセスできます：
- API: `http://localhost:8000`
- APIドキュメント（Swagger UI）: `http://localhost:8000/docs`
- 代替APIドキュメント（ReDoc）: `http://localhost:8000/redoc`
- OpenAPI仕様: `http://localhost:8000/openapi.json`

### 4. Postmanでのテスト

PostmanでOAuth2認証をテストする方法については、[POSTMAN_TEST.md](./POSTMAN_TEST.md)を参照してください。

## Dockerでの実行

### Docker Composeを使用（推奨）

#### 方法1: .envファイルを使用（推奨）

1. `.env`ファイルを作成して認証情報を設定：

```bash
cp .env.example .env
# .envファイルを編集して認証情報を入力
```

2. Docker Composeで起動：

```bash
docker-compose up -d
```

#### 方法2: docker-compose.ymlに直接環境変数を設定

1. `docker-compose.yml`の`environment`セクションのコメントを外して、実際の値を設定：

```yaml
environment:
  RMS_LOGIN_ID: "your_rms_login_id"
  RMS_PASSWORD: "your_rms_password"
  RAKUTEN_USER_ID: "your_rakuten_user_id"
  RAKUTEN_PASSWORD: "your_rakuten_password"
```

2. Docker Composeで起動：

```bash
docker-compose up -d
```

3. ログを確認：

```bash
docker-compose logs -f
```

4. 停止：

```bash
docker-compose down
```

### Dockerコマンドで直接実行

1. イメージをビルド：

```bash
docker build -t rms-rpp-api .
```

2. コンテナを起動：

```bash
docker run -d \
  --name rms-rpp-api \
  -p 8000:8000 \
  --env-file .env \
  --shm-size=2gb \
  --security-opt seccomp=unconfined \
  rms-rpp-api
```

3. ログを確認：

```bash
docker logs -f rms-rpp-api
```

4. 停止：

```bash
docker stop rms-rpp-api
docker rm rms-rpp-api
```

## エンドポイント

### POST /token

OAuth2トークンを取得するエンドポイント（ログイン）。このトークンを使用して保護されたエンドポイントにアクセスします。

#### リクエスト

- Content-Type: `application/x-www-form-urlencoded`
- Body:
  - `username`: ユーザー名
  - `password`: パスワード

#### レスポンス

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 使用例

```bash
# トークンを取得
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password"
```

### GET /users/me

現在の認証済みユーザー情報を取得します（認証が必要）。

#### 使用例

```bash
# トークンを使用してユーザー情報を取得
curl "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### GET /rpp-report

指定された日付のレポートCSVを取得します（認証が必要）。

#### パラメータ

- `date` (必須): 取得するレポートの日付 (YYYY-MM-DD形式)
  - 例: `2024-01-01`
- `report_type` (任意): 取得するレポート種別
  - `rpp`（デフォルト）: RPPレポート `https://ad.rms.rakuten.co.jp/rpp/reports`
  - `rpp-exp` または `rppexp`: RPP-EXPレポート `https://ad.rms.rakuten.co.jp/rppexp/reports/`
  - `cpnadv`: 運用型クーポン広告（クーポンアドバンス） `https://ad.rms.rakuten.co.jp/cpnadv/top`
  - `tda`: ターゲティングディスプレイ広告（TDA） `https://ad.rms.rakuten.co.jp/tda/top`
  - `tdaexp`: ターゲティングディスプレイ広告 -エクスパンション `https://ad.rms.rakuten.co.jp/tdaexp/top/`
  - `cpa`: 効果保証型広告（楽天CPA広告） `https://ad.rms.rakuten.co.jp/cpa/reports`

#### ヘッダー

- `Authorization: Bearer YOUR_ACCESS_TOKEN` (必須)

#### レスポンス

- 成功時: CSVファイル（Content-Type: text/csv）
- エラー時: JSON形式のエラーメッセージ

#### 使用例

```bash
# 1. まずトークンを取得
TOKEN=$(curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password" | jq -r '.access_token')

# 2. トークンを使用してレポートを取得（例: RPP-EXP）
curl "http://localhost:8000/rpp-report?date=2024-01-01&report_type=rpp-exp" \
  -H "Authorization: Bearer $TOKEN" \
  -o rpp-exp_report_2024-01-01.csv
```

#### エラーレスポンス

- `400 Bad Request`: 無効な日付形式
- `401 Unauthorized`: 認証が必要、またはトークンが無効
- `404 Not Found`: 指定された日付のレポートが見つからない
- `500 Internal Server Error`: サーバー内部エラー

## n8nとの連携

このAPIはn8nのOAuth2認証に対応しています。詳細な設定方法については、[N8N_SETUP.md](./N8N_SETUP.md)を参照してください。

### クイックスタート（Client Credentialsフロー）

1. n8nのHTTP Requestノードで「OAuth2 API」認証を選択
2. **Grant Type**: `Client Credentials` ⭐ **重要**
3. **Access Token URL**: `http://your-api-server:8000/token`
4. **Client ID**: 環境変数で設定したクライアントID（例: `n8n`）
5. **Client Secret**: 環境変数で設定したクライアントシークレット（例: `n8n-secret`）

**注意**: Client Credentialsフローでは、Username/Passwordは不要です。

## 注意事項

- このAPIは、楽天RMSへのログインとレポートのダウンロード処理を行うため、実行に時間がかかる場合があります。
- 環境変数から認証情報を取得するため、適切な環境変数が設定されている必要があります。
- ブラウザの自動化処理（Playwright）を使用するため、適切な環境が整っている必要があります。
- 本番環境では必ず `SECRET_KEY` を強力なランダム文字列に変更してください。
- CORS設定は環境変数 `CORS_ORIGINS` で制御できます（デフォルト: `*`）。

