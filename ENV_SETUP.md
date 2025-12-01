# 環境変数（.envファイル）の設定ガイド

## .envファイルの配置場所

`.env`ファイルは**プロジェクトのルートディレクトリ**に配置してください。

```
rms-rpp-api/
├── .env              ← ここに配置
├── main.py
├── config.py
├── auth.py
├── requirements.txt
└── ...
```

## 設定方法

### 1. ローカル開発環境

プロジェクトルートに`.env`ファイルを作成：

```bash
# プロジェクトルートで実行
cd /home/tatuhisa/sepply/rms-rpp-api
touch .env
```

`.env`ファイルの内容例：

```bash
# RMS認証情報
RMS_LOGIN_ID=your_rms_login_id
RMS_PASSWORD=your_rms_password

# 楽天会員認証情報
RAKUTEN_USER_ID=your_rakuten_user_id
RAKUTEN_PASSWORD=your_rakuten_password

# OAuth2設定
SECRET_KEY=your-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth2クライアント設定（Client Credentialsフロー用）
OAUTH_CLIENT_ID=n8n
OAUTH_CLIENT_SECRET=n8n-secret
OAUTH_CLIENT_SCOPE=read

# OAuth2ユーザー設定（Password Credentialsフロー用、オプション）
OAUTH_USERNAME=admin
OAUTH_PASSWORD=admin
OAUTH_EMAIL=admin@example.com

# CORS設定
CORS_ORIGINS=http://localhost:3000,http://localhost:5678
```

### 2. Dockerコンテナでの使用

#### 方法1: docker-composeを使用（推奨）

`docker-compose.yml`で自動的に`.env`ファイルを読み込みます：

```bash
# プロジェクトルートに.envファイルを配置
docker-compose up -d
```

#### 方法2: docker runで直接指定

```bash
# プロジェクトルートから実行
docker run -p 8000:8000 --env-file .env rms-rpp-api:latest
```

#### 方法3: 環境変数を直接指定

```bash
docker run -p 8000:8000 \
  -e RMS_LOGIN_ID=your_rms_login_id \
  -e RMS_PASSWORD=your_rms_password \
  -e SECRET_KEY=your-secret-key \
  rms-rpp-api:latest
```

### 3. Nuitkaでコンパイルした実行ファイル

Nuitkaでコンパイルした実行ファイルの場合、`.env`ファイルは以下の順序で検索されます：

1. **実行ファイルと同じディレクトリ**（推奨）
2. **プロジェクトルート**（元の`.env`ファイルの場所）
3. **実行時のカレントディレクトリ**

#### スタンドアロンモード（`dist/main.dist/rms-rpp-api.bin`）の場合

```bash
# 方法1: 実行ファイルと同じディレクトリに配置（推奨）
cp .env dist/main.dist/.env
cd dist/main.dist
./rms-rpp-api.bin

# 方法2: プロジェクトルートの.envを使用（元の場所）
cd /home/tatuhisa/sepply/rms-rpp-api
./dist/main.dist/rms-rpp-api.bin

# 方法3: 環境変数を直接設定
export RMS_LOGIN_ID=your_rms_login_id
export RMS_PASSWORD=your_rms_password
./dist/main.dist/rms-rpp-api.bin
```

#### ワンファイルモード（`dist/rms-rpp-api`）の場合

**重要**: ワンファイルモードでは、実行時のカレントディレクトリの`.env`ファイルが優先的に読み込まれます。

```bash
# 方法1: 実行ファイルと同じディレクトリに配置して実行（推奨）
cp .env dist/.env
cd dist
./rms-rpp-api

# 方法2: プロジェクトルートの.envを使用（カレントディレクトリがプロジェクトルートの場合）
cd /home/tatuhisa/sepply/rms-rpp-api
./dist/rms-rpp-api

# 方法3: 環境変数を直接設定
export RMS_LOGIN_ID=your_rms_login_id
export RMS_PASSWORD=your_rms_password
cd dist
./rms-rpp-api
```

**注意**: `cd dist && ./rms-rpp-api`のように実行する場合、`dist/.env`が読み込まれます。

**推奨**: 実行ファイルと同じディレクトリに`.env`ファイルを配置すると、どこから実行しても動作します。

### 4. Dockerイメージとして配布する場合

**重要**: `.env`ファイルはDockerイメージに含めないでください（セキュリティ上の理由）。

#### 実行時に環境変数を渡す

```bash
# 方法1: --env-fileオプションを使用
docker run -p 8000:8000 --env-file .env your-username/rms-rpp-api:latest

# 方法2: 環境変数を直接指定
docker run -p 8000:8000 \
  -e RMS_LOGIN_ID=your_rms_login_id \
  -e RMS_PASSWORD=your_rms_password \
  -e SECRET_KEY=your-secret-key \
  your-username/rms-rpp-api:latest

# 方法3: docker-composeを使用
docker-compose -f docker-compose.nuitka.yml up -d
```

## セキュリティに関する注意

1. **`.env`ファイルをGitにコミットしない**
   - `.gitignore`に`.env`を追加してください
   - 機密情報が含まれているため、リポジトリに含めないでください

2. **Dockerイメージに含めない**
   - `.env`ファイルをDockerfileでCOPYしないでください
   - 実行時に`--env-file`オプションで渡してください

3. **本番環境では環境変数管理サービスを使用**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Kubernetes Secrets
   など

## .gitignoreの確認

`.gitignore`に以下が含まれていることを確認してください：

```
.env
.env.local
.env.*.local
```

## トラブルシューティング

### .envファイルが読み込まれない

1. **ファイルの場所を確認**
   ```bash
   # プロジェクトルートに配置されているか確認
   ls -la .env
   ```

2. **ファイルの権限を確認**
   ```bash
   # 読み取り権限があるか確認
   chmod 644 .env
   ```

3. **環境変数が正しく設定されているか確認**
   ```bash
   # Pythonで確認
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('RMS_LOGIN_ID'))"
   ```

### Dockerコンテナで環境変数が読み込まれない

1. **docker-compose.ymlの設定を確認**
   ```yaml
   env_file:
     - .env  # この行がコメントアウトされていないか確認
   ```

2. **.envファイルのパスを確認**
   - `docker-compose.yml`と同じディレクトリに`.env`ファイルがあることを確認

3. **環境変数を直接指定してテスト**
   ```bash
   docker run -p 8000:8000 -e RMS_LOGIN_ID=test rms-rpp-api:latest
   ```

