# Playwright用のPythonベースイメージを使用
FROM mcr.microsoft.com/playwright/python:v1.39.0-jammy

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係はPlaywrightベースイメージに含まれているため不要
# 必要に応じて追加のパッケージをインストール可能

# Pythonの依存関係をコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# Playwrightのブラウザをインストール
RUN playwright install chromium
RUN playwright install-deps chromium

# アプリケーションコードをコピー
COPY . .

# ポート8000を公開
EXPOSE 8000

# アプリケーションを起動
# uvicornコマンドを直接使用（推奨）
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

