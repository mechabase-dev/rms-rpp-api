"""
楽天RMS RPPレポートAPI
日付パラメータを受け取り、その日付のCSVファイルを返すAPI
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks, Depends, Request, Form
from fastapi.responses import Response, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import logging
from typing import Optional
import os
import tempfile
import shutil
import base64

from rpp_service import get_rpp_report_csv as fetch_rpp_report_csv
from config import get_rms_credentials, get_rakuten_credentials
from auth import (
    authenticate_user,
    authenticate_client,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_active_user,
    get_users_db,
    get_clients_db,
    Token,
    User,
    Client,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="楽天RMS RPPレポートAPI",
    description="日付パラメータを受け取り、その日付のCSVファイルを返すAPI",
    version="1.0.0"
)

# CORS設定（n8nなどの外部ツールからのアクセスを許可）
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RefreshTokenRequest(BaseModel):
    """リフレッシュトークンリクエストモデル"""
    refresh_token: str


@app.get("/")
async def root():
    """APIのルートエンドポイント"""
    return {
        "message": "楽天RMS RPPレポートAPI",
        "endpoints": {
            "/token": "OAuth2トークンを取得（ログイン）",
            "/token/refresh": "リフレッシュトークンで新しいアクセストークンを取得",
            "/token/info": "トークン情報を取得",
            "/.well-known/oauth-authorization-server": "OAuth2メタデータ",
            "/rpp-report": "日付パラメータを受け取り、CSVファイルを返す（認証必要）",
            "/users/me": "現在のユーザー情報を取得"
        }
    }


@app.post("/token", response_model=Token)
async def get_access_token(
    request: Request,
    grant_type: str = Form(...),
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    scope: Optional[str] = Form("read")
):
    """
    OAuth2トークンを取得するエンドポイント
    Resource Owner Password Credentials と Client Credentials の両方をサポート
    
    Args:
        request: リクエストオブジェクト
        grant_type: OAuth2 Grant Type (password または client_credentials)
        username: ユーザー名（grant_type=passwordの場合）
        password: パスワード（grant_type=passwordの場合）
        client_id: クライアントID（grant_type=client_credentialsの場合）
        client_secret: クライアントシークレット（grant_type=client_credentialsの場合）
        scope: スコープ（オプション、デフォルト: read）
    
    Returns:
        Token: アクセストークン、トークンタイプ
    """
    scope_str = scope if scope else "read"
    
    # Client Credentials フロー
    if grant_type == "client_credentials":
        if not client_id or not client_secret:
            # Basic認証から取得を試みる
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Basic "):
                try:
                    encoded = auth_header.split(" ")[1]
                    decoded = base64.b64decode(encoded).decode("utf-8")
                    client_id, client_secret = decoded.split(":", 1)
                except Exception:
                    pass
        
        if not client_id or not client_secret:
            raise HTTPException(
                status_code=401,
                detail="クライアントIDとクライアントシークレットが必要です",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        client = authenticate_client(client_id, client_secret)
        if not client:
            raise HTTPException(
                status_code=401,
                detail="無効なクライアントIDまたはクライアントシークレットです",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        # クライアントのスコープを使用（指定されていない場合）
        if not scope or scope == "read":
            scope_str = client.scope
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": client_id, "client_id": client_id, "scope": scope_str, "grant_type": "client_credentials"},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "scope": scope_str
        }
    
    # Resource Owner Password Credentials フロー
    elif grant_type == "password":
        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="ユーザー名とパスワードが必要です"
            )
        
        users_db = get_users_db()
        user = authenticate_user(users_db, username, password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="ユーザー名またはパスワードが正しくありません",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "scope": scope_str},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_token": refresh_token,
            "scope": scope_str
        }
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"サポートされていないGrant Typeです: {grant_type}"
        )


@app.post("/token/refresh", response_model=Token)
async def refresh_access_token(refresh_request: RefreshTokenRequest):
    """
    リフレッシュトークンを使用して新しいアクセストークンを取得
    
    Args:
        refresh_request: リフレッシュトークンを含むリクエスト
    
    Returns:
        Token: 新しいアクセストークンとリフレッシュトークン
    """
    payload = verify_token(refresh_request.refresh_token, "refresh")
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="無効または期限切れのリフレッシュトークンです",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="無効なトークンです")
    
    users_db = get_users_db()
    user = users_db.get(username)
    if not user:
        raise HTTPException(status_code=401, detail="ユーザーが見つかりません")
    
    scope_str = payload.get("scope", "read")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scope": scope_str},
        expires_delta=access_token_expires
    )
    # 新しいリフレッシュトークンも発行
    new_refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": new_refresh_token,
        "scope": scope_str
    }


@app.get("/token/info")
async def get_token_info(current_user: User = Depends(get_current_active_user)):
    """
    現在のトークン情報を取得
    
    Args:
        current_user: 現在の認証済みユーザー
    
    Returns:
        トークン情報
    """
    return {
        "username": current_user.username,
        "email": current_user.email,
        "active": not current_user.disabled
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata(request: Request):
    """
    OAuth2メタデータエンドポイント（n8nなどのOAuth2クライアント用）
    """
    base_url = str(request.base_url).rstrip('/')
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "response_types_supported": ["code", "token"],
        "grant_types_supported": ["authorization_code", "password", "refresh_token", "client_credentials"],
        "scopes_supported": ["read", "write"],
        "token_endpoint_auth_signing_alg_values_supported": ["HS256"]
    }


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """現在のユーザー情報を取得"""
    return current_user


def cleanup_temp_directory(temp_dir: str):
    """一時ディレクトリを削除するバックグラウンドタスク"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"一時ディレクトリを削除しました: {temp_dir}")
    except Exception as e:
        logger.warning(f"一時ディレクトリの削除に失敗しました: {temp_dir}, エラー: {str(e)}")


@app.get("/rpp-report")
async def get_rpp_report_csv(
    date: str = Query(
        ...,
        description="取得するレポートの日付 (YYYY-MM-DD形式)",
        example="2024-01-01"
    ),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_active_user)
):
    """
    指定された日付のRPPレポートCSVを取得する（認証が必要）
    
    Args:
        date: 取得するレポートの日付 (YYYY-MM-DD形式)
        current_user: 現在の認証済みユーザー
    
    Returns:
        CSVファイルのレスポンス
    """
    try:
        # 日付の検証
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"無効な日付形式です。YYYY-MM-DD形式で指定してください。例: 2024-01-01"
            )
        
        logger.info(f"RPPレポート取得リクエスト: 日付={target_date}")
        
        # 一時ディレクトリを作成
        temp_dir = tempfile.mkdtemp(prefix="rpp_report_")
        download_dir = os.path.join(temp_dir, "downloads")
        
        try:
            # 認証情報を取得
            try:
                rms_credentials = get_rms_credentials()
                rakuten_credentials = get_rakuten_credentials()
            except ValueError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"認証情報の取得に失敗しました: {str(e)}"
                )
            
            # RPPレポートを取得
            csv_file_path = await fetch_rpp_report_csv(
                rms_credentials=rms_credentials,
                rakuten_credentials=rakuten_credentials,
                target_date=target_date,
                download_dir=download_dir,
                headless=True
            )
            
            if not csv_file_path or not os.path.exists(csv_file_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"指定された日付 ({date}) のレポートが見つかりませんでした。"
                )
            
            # ファイル名を生成
            filename = f"rpp_report_{date}.csv"
            
            logger.info(f"CSVファイルを返します: {csv_file_path}")
            
            # CSVファイルを読み込む
            with open(csv_file_path, 'rb') as f:
                csv_content = f.read()
            
            # バックグラウンドタスクで一時ディレクトリを削除
            background_tasks.add_task(cleanup_temp_directory, temp_dir)
            
            # CSVファイルを返す
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
            
        except Exception as e:
            logger.error(f"レポート取得中にエラーが発生しました: {str(e)}")
            # エラー時も一時ディレクトリをクリーンアップ
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
            raise HTTPException(
                status_code=500,
                detail=f"レポート取得中にエラーが発生しました: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"予期しないエラーが発生しました: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

