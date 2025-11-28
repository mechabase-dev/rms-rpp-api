# PostmanでのOAuth2テストガイド

このドキュメントでは、ローカル環境でAPIを起動し、PostmanでOAuth2認証をテストする方法を説明します。

## 1. ローカル環境のセットアップ

### 依存関係のインストール

```bash
pip install -r requirements.txt
playwright install chromium
```

### 環境変数の設定

#### 方法1: .envファイルを使用（推奨）

`.env.example`をコピーして`.env`ファイルを作成：

```bash
cp .env.example .env
```

`.env`ファイルを編集して、実際の値を設定します：

```bash
# OAuth2設定（テスト用）
SECRET_KEY=test-secret-key-for-local-development
OAUTH_CLIENT_ID=postman
OAUTH_CLIENT_SECRET=postman-secret
```

#### 方法2: 環境変数を直接設定

```bash
# OAuth2設定
export SECRET_KEY="test-secret-key-for-local-development"
export ACCESS_TOKEN_EXPIRE_MINUTES="30"

# OAuth2クライアント設定（Client Credentialsフロー用）
export OAUTH_CLIENT_ID="postman"
export OAUTH_CLIENT_SECRET="postman-secret"

# OAuth2ユーザー設定（Password Credentialsフロー用、オプション）
export OAUTH_USERNAME="admin"
export OAUTH_PASSWORD="admin"
```

**注意**: `.env`ファイルがない場合、デフォルト値が使用されます（開発用）。

### APIサーバーの起動

#### 方法1: 起動スクリプトを使用（推奨）

```bash
./start_local.sh
```

#### 方法2: uvicornを直接使用

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 方法3: Pythonで直接実行

```bash
python main.py
```

サーバーが起動すると、以下のURLでアクセスできます：
- **API**: `http://localhost:8000`
- **APIドキュメント（Swagger UI）**: `http://localhost:8000/docs`
- **代替APIドキュメント（ReDoc）**: `http://localhost:8000/redoc`
- **OpenAPI仕様**: `http://localhost:8000/openapi.json`

**Swagger UIでは、直接APIをテストできます！** `/docs`にアクセスして、各エンドポイントの「Try it out」ボタンを使用してください。

## 2. Postmanでのテスト

### 方法1: Client Credentialsフロー（推奨）

#### ステップ1: トークン取得リクエスト

1. Postmanで新しいリクエストを作成
2. **Method**: `POST`
3. **URL**: `http://localhost:8000/token`
4. **Headers**:
   - `Content-Type`: `application/x-www-form-urlencoded`
5. **Body** → `x-www-form-urlencoded`:
   - `grant_type`: `client_credentials`
   - `client_id`: `postman`
   - `client_secret`: `postman-secret`
   - `scope`: `read` (オプション)

**または、Basic認証を使用：**

1. **Authorization** タブを選択
2. **Type**: `Basic Auth`
3. **Username**: `postman`
4. **Password**: `postman-secret`
5. **Body** → `x-www-form-urlencoded`:
   - `grant_type`: `client_credentials`
   - `scope`: `read` (オプション)

#### ステップ2: レスポンスからトークンを取得

レスポンス例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "scope": "read"
}
```

#### ステップ3: 保護されたエンドポイントにアクセス

1. 新しいリクエストを作成
2. **Method**: `GET`
3. **URL**: `http://localhost:8000/rpp-report?date=2024-01-01`
4. **Authorization** タブ:
   - **Type**: `Bearer Token`
   - **Token**: ステップ2で取得した `access_token` を貼り付け

### 方法2: Password Credentialsフロー

#### ステップ1: トークン取得リクエスト

1. Postmanで新しいリクエストを作成
2. **Method**: `POST`
3. **URL**: `http://localhost:8000/token`
4. **Headers**:
   - `Content-Type`: `application/x-www-form-urlencoded`
5. **Body** → `x-www-form-urlencoded`:
   - `grant_type`: `password`
   - `username`: `admin`
   - `password`: `admin`
   - `scope`: `read` (オプション)

#### ステップ2: レスポンスからトークンを取得

レスポンス例：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "scope": "read"
}
```

#### ステップ3: 保護されたエンドポイントにアクセス

方法1と同様に、Bearer Tokenを使用してアクセスします。

### 方法3: PostmanのOAuth2ヘルパーを使用

1. リクエストの **Authorization** タブを開く
2. **Type**: `OAuth 2.0` を選択
3. **Grant Type**: `Client Credentials` を選択
4. **Access Token URL**: `http://localhost:8000/token`
5. **Client ID**: `postman`
6. **Client Secret**: `postman-secret`
7. **Scope**: `read` (オプション)
8. **Get New Access Token** をクリック
9. トークンが取得できたら、**Use Token** をクリック

## 3. テスト用エンドポイント

### トークン情報取得

```
GET http://localhost:8000/token/info
Authorization: Bearer {access_token}
```

### ユーザー情報取得（Password Credentialsフローのみ）

```
GET http://localhost:8000/users/me
Authorization: Bearer {access_token}
```

### OAuth2メタデータ取得

```
GET http://localhost:8000/.well-known/oauth-authorization-server
```

## 4. Postman Collectionの例

以下のJSONをPostmanにインポートできます：

```json
{
  "info": {
    "name": "RMS RPP API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Get Token (Client Credentials)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/x-www-form-urlencoded"
          }
        ],
        "body": {
          "mode": "urlencoded",
          "urlencoded": [
            {
              "key": "grant_type",
              "value": "client_credentials"
            },
            {
              "key": "client_id",
              "value": "postman"
            },
            {
              "key": "client_secret",
              "value": "postman-secret"
            },
            {
              "key": "scope",
              "value": "read"
            }
          ]
        },
        "url": {
          "raw": "http://localhost:8000/token",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["token"]
        }
      }
    },
    {
      "name": "Get RPP Report",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}",
            "type": "text"
          }
        ],
        "url": {
          "raw": "http://localhost:8000/rpp-report?date=2024-01-01",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["rpp-report"],
          "query": [
            {
              "key": "date",
              "value": "2024-01-01"
            }
          ]
        }
      }
    },
    {
      "name": "Get Token Info",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}",
            "type": "text"
          }
        ],
        "url": {
          "raw": "http://localhost:8000/token/info",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["token", "info"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "access_token",
      "value": "",
      "type": "string"
    }
  ]
}
```

## 5. トラブルシューティング

### エラー: "クライアントIDとクライアントシークレットが必要です"

- 環境変数 `OAUTH_CLIENT_ID` と `OAUTH_CLIENT_SECRET` が設定されているか確認
- リクエストのBodyに `client_id` と `client_secret` が含まれているか確認

### エラー: "無効なクライアントIDまたはクライアントシークレットです"

- クライアントIDとシークレットが環境変数と一致しているか確認
- デフォルト値（`postman/postman-secret`）を使用している場合、環境変数が設定されていない可能性があります

### エラー: "認証情報を検証できませんでした"

- トークンが期限切れの可能性があります。新しいトークンを取得してください
- トークンが正しくコピーされているか確認してください

### サーバーが起動しない

- ポート8000が既に使用されている場合は、別のポートを指定：
  ```bash
  uvicorn main:app --reload --port 8001
  ```
- 依存関係がインストールされているか確認：
  ```bash
  pip install -r requirements.txt
  ```

## 6. クイックテストコマンド

### curlを使用したテスト

```bash
# トークン取得（Client Credentials）
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=postman&client_secret=postman-secret&scope=read"

# トークンを使用してAPIにアクセス
curl -X GET "http://localhost:8000/rpp-report?date=2024-01-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### トークンを環境変数に保存

```bash
# トークンを取得して環境変数に保存
export ACCESS_TOKEN=$(curl -s -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=postman&client_secret=postman-secret" \
  | jq -r '.access_token')

# 使用
curl -X GET "http://localhost:8000/rpp-report?date=2024-01-01" \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

