#!/bin/bash
# NuitkaでコンパイルしたDockerイメージをビルドして配布するスクリプト

set -e

IMAGE_NAME="${IMAGE_NAME:-rms-rpp-api}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-}"

echo "🐳 Nuitkaコンパイル済みDockerイメージをビルドします..."

# イメージ名の構築
if [ -n "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
else
    FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
fi

echo "📦 イメージ名: ${FULL_IMAGE_NAME}"

# Dockerイメージをビルド
echo "🔨 Dockerイメージをビルド中..."
docker build -f Dockerfile.nuitka -t "${FULL_IMAGE_NAME}" .

echo ""
echo "✅ ビルドが完了しました！"
echo ""

# イメージのサイズを表示
echo "📊 イメージサイズ:"
docker images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo ""
echo "🚀 実行方法:"
echo "  docker run -p 8000:8000 --env-file .env ${FULL_IMAGE_NAME}"
echo ""

# プッシュするか確認
if [ -n "$REGISTRY" ]; then
    echo "📤 Dockerレジストリにプッシュしますか？ (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "📤 プッシュ中..."
        docker push "${FULL_IMAGE_NAME}"
        echo "✅ プッシュが完了しました！"
    fi
fi

echo ""
echo "💡 使用方法:"
echo "  # ローカルで実行"
echo "  docker run -p 8000:8000 --env-file .env ${FULL_IMAGE_NAME}"
echo ""
echo "  # Docker Hubにプッシュする場合"
echo "  REGISTRY=your-username IMAGE_NAME=rms-rpp-api ./build_and_push_docker.sh"
echo ""
echo "  # プライベートレジストリにプッシュする場合"
echo "  REGISTRY=registry.example.com IMAGE_NAME=rms-rpp-api ./build_and_push_docker.sh"


