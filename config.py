"""
設定管理
環境変数から認証情報を取得する
"""
import json
import os
from pathlib import Path
from typing import Dict

# .envファイルの読み込み（存在する場合）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenvがインストールされていない場合はスキップ


def get_rms_credentials() -> Dict[str, str]:
    """
    環境変数からRMS認証情報を取得する
    
    Returns:
        Dict[str, str]: RMS認証情報（login_id, password）
    
    Raises:
        ValueError: 必要な環境変数が設定されていない場合
    """
    login_id = os.getenv("RMS_LOGIN_ID")
    password = os.getenv("RMS_PASSWORD")
    
    if not login_id or not password:
        # JSON形式の環境変数もサポート
        rms_creds_json = os.getenv("RMS_CREDENTIALS")
        if rms_creds_json:
            try:
                creds = json.loads(rms_creds_json)
                login_id = creds.get("login_id") or creds.get("loginId")
                password = creds.get("password")
            except json.JSONDecodeError:
                pass
    
    if not login_id or not password:
        raise ValueError(
            "RMS認証情報が設定されていません。"
            "環境変数 RMS_LOGIN_ID と RMS_PASSWORD を設定するか、"
            "RMS_CREDENTIALS にJSON形式で設定してください。"
        )
    
    return {
        "login_id": login_id,
        "password": password
    }


def get_rakuten_credentials() -> Dict[str, str]:
    """
    環境変数から楽天会員認証情報を取得する
    
    Returns:
        Dict[str, str]: 楽天会員認証情報（user_id, password）
    
    Raises:
        ValueError: 必要な環境変数が設定されていない場合
    """
    user_id = os.getenv("RAKUTEN_USER_ID")
    password = os.getenv("RAKUTEN_PASSWORD")
    
    if not user_id or not password:
        # JSON形式の環境変数もサポート
        rakuten_creds_json = os.getenv("RAKUTEN_CREDENTIALS")
        if rakuten_creds_json:
            try:
                creds = json.loads(rakuten_creds_json)
                user_id = creds.get("user_id") or creds.get("userId")
                password = creds.get("password")
            except json.JSONDecodeError:
                pass
    
    if not user_id or not password:
        raise ValueError(
            "楽天会員認証情報が設定されていません。"
            "環境変数 RAKUTEN_USER_ID と RAKUTEN_PASSWORD を設定するか、"
            "RAKUTEN_CREDENTIALS にJSON形式で設定してください。"
        )
    
    return {
        "user_id": user_id,
        "password": password
    }


def get_oauth_settings() -> Dict[str, str]:
    """
    OAuth2設定を取得する
    
    Returns:
        Dict[str, str]: OAuth2設定（secret_key, algorithm, access_token_expire_minutes）
    """
    return {
        "secret_key": os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production"),
        "algorithm": os.getenv("ALGORITHM", "HS256"),
        "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    }

