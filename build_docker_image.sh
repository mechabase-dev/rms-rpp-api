#!/bin/bash
set -e

IMAGE_NAME="rms-rpp-api"

echo "🔨 Dockerイメージをビルド中..."
echo "使用するDockerfile: Dockerfile.nuitka"

docker build -f Dockerfile.nuitka -t $IMAGE_NAME .

echo ""
echo "✅ ビルドが完了しました！"
echo ""
echo "🚀 実行方法:"
echo "  docker run -p 8000:8000 --env-file .env $IMAGE_NAME"
