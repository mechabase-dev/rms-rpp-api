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
    import sys
    import os
    
    # .envファイルを探す（複数の場所をチェック）
    env_paths = []
    
    # 実行ファイルの場合と通常のPython実行の場合でパスを調整
    if getattr(sys, 'frozen', False):
        # Nuitkaでコンパイルされた実行ファイルの場合
        executable_path = Path(sys.executable)
        
        # ワンファイルモードの場合、一時ディレクトリではなく元の実行ファイルの場所を探す
        # sys.executableは一時ディレクトリ内のパスになるため、元のパスを取得
        if hasattr(sys, '_MEIPASS'):
            # PyInstallerの場合
            base_path = Path(sys.executable).parent
        else:
            # Nuitkaの場合
            # 実行ファイルの実際のパスを取得（シンボリックリンクを解決）
            try:
                real_executable = os.path.realpath(sys.executable)
                base_path = Path(real_executable).parent
            except:
                base_path = Path(sys.executable).parent
    else:
        # 通常のPython実行の場合
        base_path = Path(__file__).parent
    
    # .envファイルを探す場所のリスト
    env_paths = [
        base_path / '.env',  # 実行ファイル/スクリプトと同じディレクトリ
        base_path.parent / '.env',  # 親ディレクトリ（プロジェクトルート）
        Path.cwd() / '.env',  # カレントディレクトリ（実行時の作業ディレクトリ）
    ]
    
    # ワンファイルモードの場合、元の実行ファイルの場所も追加でチェック
    if getattr(sys, 'frozen', False) and not hasattr(sys, '_MEIPASS'):
        # Nuitkaワンファイルモードの場合、環境変数から元のパスを取得
        original_executable = os.environ.get('NUITKA_ORIGINAL_EXECUTABLE')
        if original_executable:
            env_paths.insert(0, Path(original_executable).parent / '.env')
    
    # カレントディレクトリを最優先でチェック（実行時の作業ディレクトリ）
    # これにより、cd dist && ./rms-rpp-api のように実行した場合に dist/.env を読み込める
    cwd_env = Path.cwd() / '.env'
    if cwd_env.exists() and cwd_env.is_file():
        load_dotenv(cwd_env, override=True)
    else:
        # .envファイルを読み込む（最初に見つかったものを使用）
        for env_path in env_paths:
            if env_path.exists() and env_path.is_file():
                load_dotenv(env_path, override=True)
                break
except ImportError:
    pass  # python-dotenvがインストールされていない場合はスキップ
except Exception as e:
    # エラーが発生しても処理を続行（環境変数が直接設定されている場合もあるため）
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f".envファイルの読み込み中にエラーが発生しました: {str(e)}")


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

