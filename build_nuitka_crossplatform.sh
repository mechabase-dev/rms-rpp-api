#!/bin/bash
# Nuitkaを使用してクロスプラットフォーム互換性の高いビルドを行うスクリプト

set -e

echo "🔨 Nuitkaでクロスプラットフォーム互換ビルドを開始します..."

# 必要なツールのチェック
MISSING_TOOLS=()

if ! command -v nuitka &> /dev/null; then
    echo "❌ Nuitkaがインストールされていません。"
    echo "インストール中..."
    pip install nuitka
fi

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! command -v patchelf &> /dev/null; then
        MISSING_TOOLS+=("patchelf")
    fi
fi

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "❌ 以下のツールがインストールされていません:"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo "   - $tool"
    done
    echo ""
    echo "インストール方法:"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  Ubuntu/Debian: sudo apt-get install patchelf"
    fi
    exit 1
fi

# ビルドディレクトリをクリーンアップ
echo "🧹 古いビルドファイルを削除中..."
rm -rf build dist main.dist main.build

echo "📦 Nuitkaでクロスプラットフォーム互換ビルド中..."
echo "   注意: より広い互換性を得るには、古いglibcバージョンのシステムでビルドすることを推奨します"

# クロスプラットフォーム互換性を高めるオプション
nuitka \
    --standalone \
    --onefile \
    --enable-plugin=anti-bloat \
    --include-module=uvicorn \
    --include-module=fastapi \
    --include-module=starlette \
    --include-module=pydantic \
    --include-module=playwright \
    --include-module=playwright.async_api \
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
    --output-dir=dist \
    --output-filename=rms-rpp-api \
    --linux-onefile-icon=NONE \
    main.py

echo ""
echo "✅ コンパイルが完了しました！"
echo "📁 実行ファイル: dist/rms-rpp-api"
echo ""
echo "互換性について:"
echo "  - 同じアーキテクチャ（x86_64）のLinuxで動作します"
echo "  - ビルド環境と同じかそれより新しいglibcバージョンが必要です"
echo "  - より広い互換性が必要な場合は、古いLinux（Ubuntu 18.04、CentOS 7）でビルドしてください"
echo ""
echo "実行方法:"
echo "  ./dist/rms-rpp-api"
echo ""
echo "注意: Playwrightのブラウザは別途インストールが必要です:"
echo "  playwright install chromium"

