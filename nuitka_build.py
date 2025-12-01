"""
Nuitkaビルド設定ファイル
このファイルはNuitkaのビルドオプションを定義します
"""
import os
from nuitka import Options

# スタンドアロンモードでビルド
Options.setStandaloneMode(True)

# ワンファイルモード（単一実行ファイル）
Options.setOnefileMode(True)

# プラグインを有効化
Options.plugins.add("anti-bloat")

# 必要なモジュールを明示的にインクルード
required_modules = [
    "uvicorn",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "fastapi.routing",
    "fastapi.middleware",
    "fastapi.middleware.cors",
    "starlette",
    "starlette.applications",
    "starlette.routing",
    "starlette.middleware",
    "starlette.responses",
    "pydantic",
    "playwright",
    "playwright.async_api",
    "playwright._impl",
    "dotenv",
    "jose",
    "passlib",
    "cryptography",
    "bcrypt",
]

for module in required_modules:
    Options.include_modules.add(module)



# テスト関連を除外
Options.nofollow_imports.add("test")
Options.nofollow_imports.add("tests")
Options.nofollow_imports.add("pytest")


