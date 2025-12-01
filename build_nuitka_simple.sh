#!/bin/bash
# Nuitkaを使用してPythonアプリケーションをコンパイルするシンプルなスクリプト

set -e

echo "🔨 Nuitkaでコンパイルを開始します..."

# 必要なツールのチェック
MISSING_TOOLS=()

# Nuitkaがインストールされているか確認
if ! command -v nuitka &> /dev/null; then
    echo "❌ Nuitkaがインストールされていません。"
    echo "インストール中..."
    pip install nuitka
fi

# patchelfがインストールされているか確認（Linuxの場合）
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if ! command -v patchelf &> /dev/null; then
        MISSING_TOOLS+=("patchelf")
    fi
fi

# 不足しているツールがある場合はエラー
if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    echo "❌ 以下のツールがインストールされていません:"
    for tool in "${MISSING_TOOLS[@]}"; do
        echo "   - $tool"
    done
    echo ""
    echo "インストール方法:"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  Ubuntu/Debian: sudo apt-get install patchelf"
        echo "  CentOS/RHEL: sudo yum install patchelf"
        echo "  Fedora: sudo dnf install patchelf"
    fi
    exit 1
fi

# ビルドディレクトリをクリーンアップ
echo "🧹 古いビルドファイルを削除中..."
rm -rf build dist main.dist main.build

echo "📦 Nuitkaでコンパイル中..."

# Playwrightのパスを取得
PLAYWRIGHT_PATH=$(python3 -c "import playwright; import os; print(os.path.dirname(playwright.__file__))")


# シンプルなビルド（スタンドアロン、ワンファイル）
NUITKA_CMD="nuitka \
    --standalone \
    --onefile \
    --enable-plugin=anti-bloat \
    --include-module=uvicorn \
    --include-module=fastapi \
    --include-module=starlette \
    --include-module=pydantic \
    --include-module=playwright \
    --include-module=playwright.async_api \
    --include-module=playwright._impl \
    --include-module=playwright._impl \
    --include-data-file=$PLAYWRIGHT_PATH/driver/playwright.sh=playwright/driver/playwright.sh \
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
    --output-filename=rms-rpp-api"



NUITKA_CMD="$NUITKA_CMD main.py"

# コマンドを実行
eval $NUITKA_CMD

echo ""
echo "✅ コンパイルが完了しました！"
echo ""
echo "📁 実行ファイルの場所:"
echo "  - ワンファイルモード: dist/rms-rpp-api"
echo "  - スタンドアロンモード: dist/main.dist/rms-rpp-api.bin"
echo ""
echo "実行方法:"
echo "  # ワンファイルモードの場合"
echo "  ./dist/rms-rpp-api"
echo ""
echo "  # スタンドアロンモードの場合"
echo "  ./dist/main.dist/rms-rpp-api.bin"
echo ""
echo "注意: Playwrightのブラウザは別途インストールが必要です:"
echo "  playwright install chromium"

