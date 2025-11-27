"""
楽天RMS RPPレポートAPI
日付パラメータを受け取り、その日付のCSVファイルを返すAPI
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import Response
from datetime import datetime, date
import logging
from typing import Optional
import os
import tempfile
import shutil

from rpp_service import get_rpp_report_csv as fetch_rpp_report_csv
from config import get_rms_credentials, get_rakuten_credentials

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


@app.get("/")
async def root():
    """APIのルートエンドポイント"""
    return {
        "message": "楽天RMS RPPレポートAPI",
        "endpoints": {
            "/rpp-report": "日付パラメータを受け取り、CSVファイルを返す"
        }
    }


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
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    指定された日付のRPPレポートCSVを取得する
    
    Args:
        date: 取得するレポートの日付 (YYYY-MM-DD形式)
    
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

