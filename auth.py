"""
OAuth2認証モジュール
JWTトークンを使用した認証システム
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2スキームの設定
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT設定（環境変数から取得、デフォルト値あり）
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class Token(BaseModel):
    """トークンレスポンスモデル"""
    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


class TokenData(BaseModel):
    """トークンデータモデル"""
    username: Optional[str] = None


class User(BaseModel):
    """ユーザーモデル"""
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = False


class UserInDB(User):
    """データベース内のユーザーモデル（パスワード含む）"""
    hashed_password: str


class Client(BaseModel):
    """OAuth2クライアントモデル"""
    client_id: str
    client_secret: str
    scope: Optional[str] = "read"


# 簡易的なユーザーデータベース（本番環境では実際のDBを使用）
# 環境変数からユーザー情報を取得
def get_users_db() -> Dict[str, UserInDB]:
    """
    ユーザーデータベースを取得
    環境変数からユーザー情報を読み込む
    """
    users_db: Dict[str, UserInDB] = {}
    
    # 環境変数からユーザー情報を取得
    # 形式: USER_USERNAME=admin,USER_PASSWORD=secret,USER_EMAIL=admin@example.com
    # または複数ユーザー: USERS='[{"username":"admin","password":"secret","email":"admin@example.com"}]'
    
    import json
    users_json = os.getenv("USERS")
    if users_json:
        try:
            users_list = json.loads(users_json)
            for user_data in users_list:
                username = user_data.get("username")
                password = user_data.get("password")
                email = user_data.get("email")
                if username and password:
                    hashed_password = get_password_hash(password)
                    users_db[username] = UserInDB(
                        username=username,
                        email=email,
                        hashed_password=hashed_password,
                        disabled=False
                    )
        except json.JSONDecodeError:
            pass
    
    # 単一ユーザーの環境変数もサポート
    username = os.getenv("OAUTH_USERNAME")
    password = os.getenv("OAUTH_PASSWORD")
    if username and password:
        hashed_password = get_password_hash(password)
        users_db[username] = UserInDB(
            username=username,
            email=os.getenv("OAUTH_EMAIL"),
            hashed_password=hashed_password,
            disabled=False
        )
    
    # デフォルトユーザー（開発用、本番環境では削除推奨）
    if not users_db:
        users_db["admin"] = UserInDB(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin"),
            disabled=False
        )
    
    return users_db


def get_clients_db() -> Dict[str, Client]:
    """
    OAuth2クライアントデータベースを取得
    環境変数からクライアント情報を読み込む
    """
    clients_db: Dict[str, Client] = {}
    
    import json
    # 環境変数からクライアント情報を取得
    # 形式: OAUTH_CLIENTS='[{"client_id":"n8n","client_secret":"secret123","scope":"read"}]'
    clients_json = os.getenv("OAUTH_CLIENTS")
    if clients_json:
        try:
            clients_list = json.loads(clients_json)
            for client_data in clients_list:
                client_id = client_data.get("client_id")
                client_secret = client_data.get("client_secret")
                scope = client_data.get("scope", "read")
                if client_id and client_secret:
                    clients_db[client_id] = Client(
                        client_id=client_id,
                        client_secret=client_secret,
                        scope=scope
                    )
        except json.JSONDecodeError:
            pass
    
    # 単一クライアントの環境変数もサポート
    client_id = os.getenv("OAUTH_CLIENT_ID")
    client_secret = os.getenv("OAUTH_CLIENT_SECRET")
    if client_id and client_secret:
        scope = os.getenv("OAUTH_CLIENT_SCOPE", "read")
        clients_db[client_id] = Client(
            client_id=client_id,
            client_secret=client_secret,
            scope=scope
        )
    
    # デフォルトクライアント（開発用、本番環境では削除推奨）
    if not clients_db:
        clients_db["n8n"] = Client(
            client_id="n8n",
            client_secret="n8n-secret",
            scope="read"
        )
    
    return clients_db


def authenticate_client(client_id: str, client_secret: str) -> Optional[Client]:
    """クライアントを認証"""
    clients_db = get_clients_db()
    client = clients_db.get(client_id)
    if not client:
        return None
    if client.client_secret != client_secret:
        return None
    return client


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化"""
    return pwd_context.hash(password)


def get_user(db: Dict[str, UserInDB], username: str) -> Optional[UserInDB]:
    """ユーザーを取得"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict.dict())
    return None


def authenticate_user(db: Dict[str, UserInDB], username: str, password: str) -> Optional[UserInDB]:
    """ユーザーを認証"""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """アクセストークンを生成"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """リフレッシュトークンを生成"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """トークンを検証"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """現在のユーザーを取得（トークンから）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報を検証できませんでした",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token, "access")
    if not payload:
        raise credentials_exception
    
    # Client Credentials フローの場合
    grant_type = payload.get("grant_type")
    if grant_type == "client_credentials":
        client_id = payload.get("sub") or payload.get("client_id")
        if client_id:
            # クライアントIDをユーザー名として扱う
            return User(username=client_id, email=None, disabled=False)
    
    # Resource Owner Password Credentials フローの場合
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    token_data = TokenData(username=username)
    users_db = get_users_db()
    user = get_user(users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """現在のアクティブなユーザーを取得"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="無効なユーザーです")
    return current_user

