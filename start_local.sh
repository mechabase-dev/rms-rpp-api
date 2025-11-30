#!/bin/bash
# ローカル開発環境用の起動スクリプト

echo "🚀 RMS RPP API ローカルサーバーを起動します..."

# 環境変数のデフォルト値を設定（.envファイルがない場合）
if [ ! -f .env ]; then
    echo "⚠️  .envファイルが見つかりません。デフォルト値を使用します。"
    echo ""
    echo "以下の環境変数を設定することを推奨します："
    echo "  - SECRET_KEY"
    echo "  - OAUTH_CLIENT_ID"
    echo "  - OAUTH_CLIENT_SECRET"
    echo ""
    echo "例: .envファイルを作成"
    echo "  SECRET_KEY=test-secret-key"
    echo "  OAUTH_CLIENT_ID=postman"
    echo "  OAUTH_CLIENT_SECRET=postman-secret"
    echo ""
fi

# デフォルトの環境変数を設定（.envファイルがない場合）
export SECRET_KEY=${SECRET_KEY:-"test-secret-key-for-local-development"}
export ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES:-"30"}
export OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID:-"postman"}
export OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET:-"postman-secret"}
export OAUTH_CLIENT_SCOPE=${OAUTH_CLIENT_SCOPE:-"read"}

# .envファイルがあれば読み込む
if [ -f .env ]; then
    echo "📝 .envファイルを読み込みます..."
    export $(cat .env | grep -v '^#' | xargs)
fi

echo ""
echo "✅ 設定完了"
echo ""
echo "📋 現在の設定:"
echo "  - SECRET_KEY: ${SECRET_KEY:0:20}..."
echo "  - OAUTH_CLIENT_ID: ${OAUTH_CLIENT_ID}"
echo "  - OAUTH_CLIENT_SECRET: ${OAUTH_CLIENT_SECRET}"
echo "  - ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES}"
echo ""
echo "🌐 サーバーを起動します..."
echo "   API: http://localhost:8000"
echo "   ドキュメント: http://localhost:8000/docs"
echo ""

# uvicornでサーバーを起動
uvicorn main:app --reload --host 0.0.0.0 --port 8000



