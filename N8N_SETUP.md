# n8nでのOAuth2設定ガイド

このドキュメントでは、n8nからこのAPIにOAuth2認証で接続する方法を説明します。

## 前提条件

1. APIサーバーが起動していること
2. OAuth2クライアントが設定されていること（環境変数 `OAUTH_CLIENT_ID` と `OAUTH_CLIENT_SECRET` または `OAUTH_CLIENTS`）

## n8nでの設定手順（Client Credentials フロー）

### 方法1: HTTP RequestノードでOAuth2を使用（推奨）

#### 1. HTTP Requestノードを追加

n8nのワークフローに「HTTP Request」ノードを追加します。

#### 2. OAuth2認証を設定

1. HTTP Requestノードを開き、「Authentication」セクションを展開
2. 「Authentication」を「OAuth2 API」に設定
3. 以下の情報を入力：

**基本設定:**
- **Grant Type**: `Client Credentials` ⭐ **重要：このオプションを選択**
- **Access Token URL**: `http://your-api-server:8000/token`
- **Client ID**: 環境変数で設定したクライアントID（例: `n8n`）
- **Client Secret**: 環境変数で設定したクライアントシークレット（例: `n8n-secret`）

**オプション設定:**
- **Scope**: `read` または `write`（必要に応じて）
- **Token Expires In**: `1800`（30分、秒単位）

**注意**: Client Credentialsフローでは、Username/Passwordは不要です。

#### 3. リクエスト設定

- **Method**: `GET`
- **URL**: `http://your-api-server:8000/rpp-report?date=2024-01-01`
- **Authentication**: 上記で設定したOAuth2認証を使用

### 方法2: カスタムOAuth2認証を使用

#### 1. Credentialsを作成

1. n8nの「Credentials」セクションに移動
2. 「Add Credential」をクリック
3. 「OAuth2 API」を選択

#### 2. OAuth2設定

**基本情報:**
- **Name**: `RMS RPP API OAuth2`
- **Grant Type**: `Client Credentials` ⭐ **重要：このオプションを選択**

**認証エンドポイント:**
- **Access Token URL**: `http://your-api-server:8000/token`
- **Client ID**: 環境変数で設定したクライアントID（例: `n8n`）
- **Client Secret**: 環境変数で設定したクライアントシークレット（例: `n8n-secret`）

**オプション:**
- **Scope**: `read` または `write`
- **Token Expires In**: `1800`

**注意**: Client Credentialsフローでは、Username/Passwordは不要です。

#### 3. 認証をテスト

「Test」ボタンをクリックして、認証が成功することを確認します。

#### 4. HTTP Requestノードで使用

1. HTTP Requestノードを開く
2. 「Authentication」で上記で作成したCredentialを選択
3. リクエストを設定

## エンドポイント情報

### トークン取得エンドポイント（Client Credentials フロー）

```
POST /token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

Body:
  grant_type=client_credentials
  client_id=your_client_id
  client_secret=your_client_secret
  scope=read
```

または、Basic認証ヘッダーを使用：

```
POST /token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic base64(client_id:client_secret)

Body:
  grant_type=client_credentials
  scope=read
```

**レスポンス:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "scope": "read"
}
```

**注意**: Client Credentialsフローでは、`refresh_token`は返されません。

### リフレッシュトークンエンドポイント

```
POST /token/refresh
Content-Type: application/json

Body:
{
  "refresh_token": "your_refresh_token"
}
```

### トークン情報取得エンドポイント

```
GET /token/info
Authorization: Bearer your_access_token
```

### OAuth2メタデータエンドポイント

```
GET /.well-known/oauth-authorization-server
```

## 使用例

### n8nワークフロー例

#### Client Credentialsフローを使用する場合（推奨）

1. **HTTP Requestノード（API呼び出し）**
   - Method: `GET`
   - URL: `http://your-api-server:8000/rpp-report?date={{$json.date}}`
   - Authentication: OAuth2 API
     - Grant Type: `Client Credentials`
     - Access Token URL: `http://your-api-server:8000/token`
     - Client ID: `n8n`（環境変数で設定した値）
     - Client Secret: `n8n-secret`（環境変数で設定した値）
     - Scope: `read`

n8nが自動的にトークンを取得し、リクエストに含めてくれます。

## トラブルシューティング

### 認証エラーが発生する場合

1. クライアントIDとクライアントシークレットが正しいか確認
2. 環境変数 `OAUTH_CLIENT_ID` と `OAUTH_CLIENT_SECRET` が設定されているか確認
3. Grant Typeが `Client Credentials` に設定されているか確認
4. APIサーバーが起動しているか確認

### トークンが期限切れの場合

1. リフレッシュトークンを使用して新しいアクセストークンを取得
2. または、再度ログインして新しいトークンを取得

### CORSエラーが発生する場合

n8nとAPIサーバーが異なるドメインにある場合、CORS設定が必要です。
FastAPIにCORSミドルウェアを追加してください：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## セキュリティに関する注意事項

1. **本番環境では必ず `SECRET_KEY` を強力なランダム文字列に変更してください**
2. パスワードは環境変数で管理し、コードに直接書かないでください
3. HTTPSを使用することを強く推奨します
4. トークンの有効期限を適切に設定してください

