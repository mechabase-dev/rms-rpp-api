# Nuitkaビルドガイド

このドキュメントでは、Nuitkaを使用してPythonアプリケーションをコンパイルし、ソースコードを非公開にする方法を説明します。

## 概要

NuitkaはPythonコードをC++にコンパイルし、実行可能ファイルや共有ライブラリに変換するツールです。これにより、ソースコードを非公開にできます。

## 前提条件

- Python 3.8以上
- C++コンパイラ（GCC、Clang、MSVCなど）
- 必要なシステムライブラリ
- **Linuxの場合**: `patchelf`（standaloneモードに必要）

### Linuxでのpatchelfのインストール

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install patchelf

# CentOS/RHEL
sudo yum install patchelf

# Fedora
sudo dnf install patchelf
```

## インストール

```bash
pip install nuitka
```

## ビルド方法

### 方法1: シンプルなビルド（推奨）

```bash
chmod +x build_nuitka_simple.sh
./build_nuitka_simple.sh
```

### 方法2: 詳細なビルド

```bash
chmod +x build_nuitka.sh
./build_nuitka.sh
```

### 方法3: 手動ビルド

```bash
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
    --include-module=passlib \
    --include-module=cryptography \
    --nofollow-import-to=test \
    --nofollow-import-to=tests \
    --nofollow-import-to=pytest \
    --output-dir=dist \
    --output-filename=rms-rpp-api \
    main.py
```

## Nuitkaのビルドモード

### ワンファイルモード（--onefile）とは

**ワンファイルモード**は、すべての依存関係を1つの実行ファイルにまとめるモードです。

#### 特徴

- **単一ファイル**: すべてが1つの実行ファイルに含まれる
- **配布が簡単**: 1つのファイルをコピーするだけで配布できる
- **一時ディレクトリに展開**: 実行時に一時ディレクトリ（`/tmp/onefile_*`）に展開されて実行される
- **起動がやや遅い**: 展開処理のため、起動に少し時間がかかる（通常は数秒）

#### 出力

```bash
./dist/rms-rpp-api  # 単一の実行ファイル（約60-100MB）
```

### スタンドアロンモード（--standalone）とは

**スタンドアロンモード**は、実行ファイルと依存関係をディレクトリに配置するモードです。

#### 特徴

- **ディレクトリ構造**: 実行ファイルと依存関係がディレクトリに配置される
- **起動が速い**: 展開処理がないため、起動が速い
- **配布がやや複雑**: ディレクトリ全体を配布する必要がある
- **デバッグしやすい**: ファイル構造が見えるため、問題の特定が容易

#### 出力

```bash
./dist/main.dist/
├── rms-rpp-api.bin  # 実行ファイル
├── *.so            # 共有ライブラリ
└── ...             # その他の依存関係
```

### 両方のモードを指定した場合

`--standalone --onefile` を同時に指定した場合、両方の出力が生成されることがあります：

- **ワンファイル**: `dist/rms-rpp-api`（推奨、配布しやすい）
- **スタンドアロン**: `dist/main.dist/rms-rpp-api.bin`（デバッグ用）

どちらを使用しても動作しますが、配布する場合はワンファイル（`dist/rms-rpp-api`）を推奨します。

## ビルド後の実行

### ワンファイルモード（--onefile）

```bash
./dist/rms-rpp-api
```

### スタンドアロンモード（--standalone）

```bash
./dist/main.dist/rms-rpp-api.bin
```

## 注意事項

### Playwrightの互換性

Playwrightは動的にブラウザを起動するため、Nuitkaでコンパイルした場合でも以下の点に注意が必要です：

1. **ブラウザのインストール**: コンパイル後もPlaywrightのブラウザをインストールする必要があります
   ```bash
   playwright install chromium
   ```

2. **ドライバーのインクルード**: ワンファイルモードでは、PlaywrightのNode.jsドライバーを明示的に含める必要があります
   - ビルドスクリプトが自動的に`--include-data-dir`でドライバーを含めます
   - 手動ビルドの場合は、`--include-data-dir=/path/to/playwright/driver=playwright/driver`を追加してください

3. **ドライバーパス**: Playwrightのドライバーパスが正しく設定されていることを確認してください

4. **動的インポート**: Playwrightは動的インポートを使用するため、Nuitkaの設定で適切にインクルードする必要があります

#### ワンファイルモードでのPlaywrightエラー

ワンファイルモードで`FileNotFoundError: [Errno 2] No such file or directory`が発生する場合：

1. **Playwrightドライバーが含まれていない**: ビルド時に`--include-data-dir`でドライバーを含める必要があります
2. **再ビルド**: ビルドスクリプトを更新した場合は、再ビルドしてください
3. **スタンドアロンモードを試す**: ワンファイルモードで問題が続く場合は、`--standalone`のみを使用してください

### 依存関係のインクルード

FastAPIアプリケーションをNuitkaでコンパイルする場合、以下のモジュールを明示的にインクルードする必要があります：

- `uvicorn` とそのサブモジュール
- `fastapi` とそのサブモジュール
- `starlette` とそのサブモジュール
- `pydantic`
- `playwright` とそのサブモジュール

### トラブルシューティング

#### 警告: ccacheがインストールされていない

```
Nuitka-Scons:WARNING: You are not using ccache, re-compilation of identical code will be slower than necessary.
```

この警告は問題ありません。ビルドは正常に完了しますが、再ビルド時に時間がかかる可能性があります。

**ccacheをインストールする場合（オプション）**:

```bash
# Ubuntu/Debian
sudo apt-get install ccache

# CentOS/RHEL
sudo yum install ccache

# Fedora
sudo dnf install ccache
```

ccacheをインストールすると、同じコードの再コンパイルが高速化されます。

#### エラー: モジュールが見つからない

必要なモジュールを `--include-module` または `--include-package` オプションで追加してください。

#### エラー: Playwrightが動作しない

Playwrightのドライバーデータを `--include-data-dir` で含める必要がある場合があります。

#### エラー: 実行時にエラーが発生する

デバッグモードでビルドして詳細なエラー情報を確認してください：

```bash
nuitka --standalone --debug main.py
```

## Dockerでのビルドと実行

### コンテナ化の利点

Dockerコンテナを使用することで、以下の利点があります：

1. **互換性の問題を解決**: コンテナ内で実行するため、ホストOSのglibcバージョンに依存しない
2. **環境の統一**: 開発環境と本番環境を同じにできる
3. **依存関係の管理**: 必要なライブラリをすべてコンテナに含められる

### 方法1: コンテナ内でビルド

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.39.0-jammy

WORKDIR /app

# ビルドツールをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    patchelf \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# Nuitkaでビルド
RUN nuitka --standalone --onefile \
    --include-module=uvicorn \
    --include-module=fastapi \
    --include-module=playwright \
    main.py

# 実行
CMD ["./main.bin"]
```

### 方法2: Dockerイメージとして配布（推奨）

マルチステージビルドを使用して、ソースコードを非公開にしたDockerイメージを作成します。

#### ビルドと配布

```bash
# ビルドスクリプトを使用（推奨）
chmod +x build_and_push_docker.sh
./build_and_push_docker.sh

# または、直接Dockerコマンドでビルド
docker build -f Dockerfile.nuitka -t rms-rpp-api:latest .
```

#### Dockerイメージの配布

```bash
# Docker Hubにプッシュ
docker tag rms-rpp-api:latest your-username/rms-rpp-api:latest
docker push your-username/rms-rpp-api:latest

# プライベートレジストリにプッシュ
docker tag rms-rpp-api:latest registry.example.com/rms-rpp-api:latest
docker push registry.example.com/rms-rpp-api:latest
```

#### イメージの使用

```bash
# イメージをプル
docker pull your-username/rms-rpp-api:latest

# 実行
docker run -p 8000:8000 --env-file .env your-username/rms-rpp-api:latest
```

#### 利点

- **ソースコード非公開**: コンパイル済みの実行ファイルのみがイメージに含まれる
- **軽量**: ビルドツールを含まないため、イメージサイズが小さい
- **互換性**: どのLinuxディストリビューションでも同じように動作
- **配布が簡単**: Dockerイメージとして配布できる

### 既存のDockerfileとの違い

- **通常のDockerfile**: ソースコードをそのまま実行（開発用）
- **Dockerfile.nuitka**: コンパイル済みファイルを使用（本番用、ソースコード非公開）

## 配布と互換性

### クロスプラットフォーム互換性

Nuitkaのstandaloneモードでビルドした実行ファイルは、**同じアーキテクチャ（例：x86_64）のLinuxディストリビューション間で動作する可能性が高い**ですが、完全ではありません。

#### 互換性の制約

1. **アーキテクチャ**: ビルドしたアーキテクチャ（x86_64、ARM64など）と一致する必要があります
2. **glibcバージョン**: ビルド環境のglibcバージョン以上が必要です
   - 新しいglibcでビルドしたものは、古いglibcのシステムでは動作しません
   - 逆に、古いglibcでビルドしたものは、新しいglibcのシステムでも動作します

#### 互換性を高める方法

**方法1: 古いglibcバージョンでビルド（推奨）**

古いLinuxディストリビューション（例：CentOS 7、Ubuntu 18.04）でビルドすると、より多くのシステムで動作します。

**方法2: Dockerを使用したビルド**

```dockerfile
# 古いglibcバージョンのベースイメージを使用
FROM ubuntu:18.04

WORKDIR /app
# ビルド処理...
```

**方法3: manylinux形式でビルド**

Pythonのmanylinux標準に準拠したビルドを行うことで、より広い互換性を確保できます。

#### 現在のビルド環境

- **Debian**: 通常、比較的新しいglibcバージョンを使用
- **互換性**: 同じかそれより新しいglibcバージョンのLinuxで動作
- **対象**: Ubuntu 20.04以降、Debian 11以降、CentOS 8以降など

### 配布方法

コンパイル後のファイルを配布する場合：

1. **スタンドアロンモード**: `dist/rms-rpp-api/` ディレクトリ全体を配布
2. **ワンファイルモード**: 単一の実行ファイルを配布

### 互換性の確認方法

配布先のシステムで以下を確認：

```bash
# glibcバージョンを確認
ldd --version

# アーキテクチャを確認
uname -m
```

## セキュリティに関する注意

Nuitkaでコンパイルしても、完全にソースコードを保護できるわけではありません。リバースエンジニアリングのリスクは残ります。重要な認証情報や秘密鍵は環境変数や設定ファイルで管理してください。

## 参考リンク

- [Nuitka公式ドキュメント](https://nuitka.net/doc/user-manual.html)
- [Nuitka GitHub](https://github.com/Nuitka/Nuitka)

