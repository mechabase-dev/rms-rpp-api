#!/bin/bash
# Nuitkaを使用してPythonアプリケーションをコンパイルするスクリプト

set -e

echo "🔨 Nuitkaでコンパイルを開始します..."

# Nuitkaがインストールされているか確認
if ! command -v nuitka &> /dev/null; then
    echo "❌ Nuitkaがインストールされていません。"
    echo "インストール: pip install nuitka"
    exit 1
fi

# ビルドディレクトリを作成
BUILD_DIR="build"
DIST_DIR="dist"
mkdir -p $BUILD_DIR
mkdir -p $DIST_DIR

echo "📦 依存関係をインストール中..."
pip install nuitka

echo "🔧 Nuitkaでコンパイル中..."
nuitka \
    --standalone \
    --onefile \
    --enable-plugin=anti-bloat \
    --include-module=uvicorn \
    --include-module=uvicorn.loops \
    --include-module=uvicorn.loops.auto \
    --include-module=uvicorn.protocols \
    --include-module=uvicorn.protocols.http \
    --include-module=uvicorn.protocols.http.auto \
    --include-module=uvicorn.protocols.websockets \
    --include-module=uvicorn.protocols.websockets.auto \
    --include-module=uvicorn.lifespan \
    --include-module=uvicorn.lifespan.on \
    --include-module=fastapi \
    --include-module=fastapi.routing \
    --include-module=fastapi.middleware \
    --include-module=fastapi.middleware.cors \
    --include-module=starlette \
    --include-module=starlette.applications \
    --include-module=starlette.routing \
    --include-module=starlette.middleware \
    --include-module=starlette.responses \
    --include-module=pydantic \
    --include-module=playwright \
    --include-module=playwright.async_api \
    --include-module=playwright._impl \
    --include-module=playwright._impl \
    --include-module=dotenv \
    --include-module=jose \
    --include-package=passlib \
    --include-module=passlib.handlers \
    --include-module=passlib.handlers.bcrypt \
    --include-module=cryptography \
    --include-module=bcrypt \
    --nofollow-import-to=test \
    --nofollow-import-to=tests \
    --nofollow-import-to=pytest \
    --output-dir=$BUILD_DIR \
    --output-filename=main \
    main.py

echo "✅ コンパイルが完了しました！"
echo "📁 実行ファイル: dist/rms-rpp-api"
echo ""
echo "実行方法:"
echo "  ./dist/rms-rpp-api"

