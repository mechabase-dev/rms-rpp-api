"""
RPPレポート取得サービス
楽天RMSからRPPレポートをダウンロードしてCSVファイルを取得する
"""
import asyncio
import logging
import os
import shutil
import time
import zipfile
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

REPORT_TYPES: Dict[str, Dict[str, str]] = {
    "rpp": {
        "slug": "rpp",
        "label": "RPP",
        "top_path": "top",
        "nav_selector": '#root > div > div.rpp-header > div:nth-child(2) > nav > div > div.rpp-nav > nav > ul > li:nth-child(6) > a > div',
        "report_radio_selector": "#rdReportTypeItem",
        "start_placeholder": "Select start",
        "end_placeholder": "Select end",
        "download_button_selectors": [
            'button:has-text("全商品レポートダウンロード")',
            'button:has-text("ダウンロード")'
        ],
        "history_link_text": "ダウンロード履歴",
    },
    "rppexp": {
        "slug": "rppexp",
        "label": "RPP-EXP",
        "top_path": "top",
        "nav_selector": '#root > div > div.rpp-header > div:nth-child(2) > nav > div > div.rpp-nav > nav > ul > li:nth-child(6) > a > div',
        "report_radio_selector": "#rdReportTypeItem",
        "start_placeholder": "Select start",
        "end_placeholder": "Select end",
        "download_button_selectors": [
            'button:has-text("全商品レポートダウンロード")',
            'button:has-text("ダウンロード")'
        ],
        "history_link_text": "ダウンロード履歴",
    },
    "rpp-exp": {"alias": "rppexp"},
    "cpnadv": {
        "slug": "cpnadv",
        "label": "クーポンアドバンス",
        "top_path": "top",
        "download_button_selectors": [
            'button:has-text("ダウンロード")',
            'a:has-text("ダウンロード")'
        ],
        "history_link_text": "ダウンロード履歴",
    },
    "tda": {
        "slug": "tda",
        "label": "TDA",
        "top_path": "top",
        "download_button_selectors": [
            'button:has-text("ダウンロード")',
            'a:has-text("ダウンロード")'
        ],
        "history_link_text": "ダウンロード履歴",
    },
    "tdaexp": {
        "slug": "tdaexp",
        "label": "TDA-EXP",
        "top_path": "top",
        "download_button_selectors": [
            'button:has-text("ダウンロード")',
            'a:has-text("ダウンロード")'
        ],
        "history_link_text": "ダウンロード履歴",
    },
    "cpa": {
        "slug": "cpa",
        "label": "楽天CPA",
        "top_path": "reports",
        "download_button_selectors": [
            'button:has-text("ダウンロード")',
            'a:has-text("ダウンロード")'
        ],
        "history_link_text": "ダウンロード履歴",
    },
}


async def login_to_rms(
    page,
    rms_creds: dict,
    rakuten_creds: dict,
    screenshot_dir: Optional[Path] = None
) -> None:
    """
    RMSにログインする共通関数
    
    Args:
        page: Playwrightのページオブジェクト
        rms_creds (dict): RMSの認証情報（login_id, password）
        rakuten_creds (dict): 楽天会員の認証情報（user_id, password）
        screenshot_dir (Path): スクリーンショット保存ディレクトリ（オプション）
    """
    import traceback
    
    # 認証情報の取得
    login_id = rms_creds.get("login_id")
    password = rms_creds.get("password")
    rakuten_user_id = rakuten_creds.get("user_id")
    rakuten_user_password = rakuten_creds.get("password")

    if not all([login_id, password, rakuten_user_id, rakuten_user_password]):
        missing = [k for k, v in {"RMS login_id": login_id, "RMS password": password, "Rakuten user_id": rakuten_user_id, "Rakuten password": rakuten_user_password}.items() if not v]
        raise ValueError(f"認証情報辞書に必要なキーが不足しています: {', '.join(missing)}")
    
    try:
        # RMSログインページに移動
        logger.info("RMSログインページに移動します...")
        current_url = page.url
        logger.info(f"現在のURL: {current_url}")
        
        await page.goto("https://glogin.rms.rakuten.co.jp/", timeout=90000)
        logger.info("RMSログインページへの移動が完了しました")
        logger.info(f"遷移後のURL: {page.url}")
        
        # ページのタイトルを確認
        title = await page.title()
        logger.info(f"ページタイトル: {title}")
        
        # RMSログイン情報を入力
        logger.info("RMSログイン情報を入力します...")
        await page.locator('input[name="login_id"]').fill(login_id)
        await page.locator('input[name="passwd"]').fill(password)
        logger.info("ログイン情報の入力が完了しました")
        
        logger.info("ログインボタンをクリックします...")
        await page.locator('button[name="submit"]').click()
        await page.wait_for_load_state('networkidle', timeout=90000)
        await asyncio.sleep(2)
        logger.info("ログインボタンのクリックが完了しました")
        logger.info(f"ログイン後のURL: {page.url}")
        
        # 楽天会員ログイン情報を入力（必要な場合）
        if await page.locator('input[name="user_id"]').is_visible(timeout=10000):
            logger.info("楽天会員ログイン情報を入力します...")
            await page.locator('input[name="user_id"]').fill(rakuten_user_id)
            await page.locator('input[name="user_passwd"]').fill(rakuten_user_password)
            await page.locator('button[name="submit"]').click()
            await page.wait_for_load_state('networkidle', timeout=90000)
            await asyncio.sleep(2)
            logger.info("楽天会員ログイン情報の入力が完了しました")
            logger.info(f"楽天会員ログイン後のURL: {page.url}")
        else:
            logger.info("楽天会員ログイン画面はスキップされました。")
        
        # 確認画面の「次へ」ボタンをクリック（必要な場合）
        next_button_selector = 'button[name="submit"]:has-text("次へ")'
        if await page.locator(next_button_selector).is_visible(timeout=10000):
            logger.info("確認画面の「次へ」ボタンをクリックします...")
            await page.locator(next_button_selector).click()
            await page.wait_for_load_state('networkidle', timeout=90000)
            await asyncio.sleep(2)
            logger.info("確認画面の「次へ」ボタンのクリックが完了しました")
            logger.info(f"確認画面後のURL: {page.url}")
        else:
            logger.info("確認画面（次へボタン）はスキップされました。")
        
        # RMSメインメニューに移動
        rms_link_selector = 'a[href*="mainmenu.rms.rakuten.co.jp"]'
        logger.info(f"RMSメインメニューリンク ({rms_link_selector}) をクリックします...")
        try:
            await page.locator(rms_link_selector).wait_for(state="visible", timeout=60000)
            await page.locator(rms_link_selector).click()
            await page.wait_for_load_state('networkidle', timeout=90000)
            await asyncio.sleep(2)
            logger.info("RMSメインメニューリンクのクリックが完了しました")
            logger.info(f"RMSメインメニュー後のURL: {page.url}")
        except Exception as e:
            logger.error("RMSメインメニューリンクが見つかりません。")
            if screenshot_dir:
                await page.screenshot(path=screenshot_dir / f"error_rms_link_not_found_{int(time.time())}.png")
            raise

        # RMS利用規約同意（表示されない場合があるため任意扱い）
        terms_button_selector = 'button[type="submit"]:has-text("RMSを利用します")'
        terms_button = page.locator(terms_button_selector)
        logger.info(f"RMS利用規約同意ボタン ({terms_button_selector}) の表示を確認します...")
        try:
            if await terms_button.is_visible(timeout=5000):
                logger.info("RMS利用規約同意ボタンが表示されたためクリックします...")
                await terms_button.click()
                await page.wait_for_load_state('networkidle', timeout=90000)
                await asyncio.sleep(2)
                logger.info("RMS利用規約同意ボタンをクリックしました。")
                logger.info(f"利用規約同意後のURL: {page.url}")
            else:
                logger.info("RMS利用規約同意ボタンは表示されませんでした。既に同意済みとみなし処理を続行します。")
        except PlaywrightTimeoutError:
            logger.info("RMS利用規約同意ボタンは時間内に表示されませんでした。既に同意済みとみなし処理を続行します。")

        # 確認画面の処理（不定期で表示される場合）
        try:
            # 確認画面のチェックボックスが表示されるかチェック
            confirm_checkbox_selector = 'input[type="checkbox"][name="confirm"]'
            if await page.locator(confirm_checkbox_selector).is_visible(timeout=10000):
                logger.info("確認画面が表示されました。チェックボックスを選択します...")
                
                # チェックボックスを選択
                await page.locator(confirm_checkbox_selector).check()
                await asyncio.sleep(1)
                logger.info("確認画面のチェックボックスを選択しました。")
                
                # 「RMSメインメニューへ進む」ボタンをクリック
                proceed_button_selector = 'button.btn-reset.btn-round.btn-red:has-text("RMSメインメニューへ進む")'
                if await page.locator(proceed_button_selector).is_visible(timeout=10000):
                    logger.info("「RMSメインメニューへ進む」ボタンをクリックします...")
                    await page.locator(proceed_button_selector).click()
                    await page.wait_for_load_state('networkidle', timeout=90000)
                    await asyncio.sleep(2)
                    logger.info("「RMSメインメニューへ進む」ボタンをクリックしました。")
                    logger.info(f"確認画面処理後のURL: {page.url}")
                else:
                    logger.warning("「RMSメインメニューへ進む」ボタンが見つかりません。")
            else:
                logger.info("確認画面は表示されませんでした。")
        except Exception as e:
            logger.warning(f"確認画面の処理中にエラーが発生しましたが、処理を続行します: {str(e)}")
            if screenshot_dir:
                await page.screenshot(path=screenshot_dir / f"warning_confirm_screen_{int(time.time())}.png")

        logger.info("ログイン処理が正常に完了しました")

    except Exception as e:
        logger.error(f"RMSログイン中にエラーが発生しました: {str(e)}")
        logger.error(f"エラーの詳細:\n{traceback.format_exc()}")
        if screenshot_dir:
            await page.screenshot(path=screenshot_dir / f"error_login_{int(time.time())}.png")
        raise


def _resolve_report_type(report_type: str) -> Dict[str, str]:
    """
    指定されたレポート種別を正規化して返す
    """
    key = (report_type or "rpp").lower()
    resolved = REPORT_TYPES.get(key)
    if resolved and "alias" in resolved:
        resolved = REPORT_TYPES.get(resolved["alias"])
    if not resolved:
        raise ValueError(f"サポートされていないレポート種別です: {report_type}. 利用可能: {', '.join(sorted(set(REPORT_TYPES.keys())))}")
    return resolved


async def navigate_to_rpp_top(
    page,
    screenshot_dir: Optional[Path] = None,
    download_dir: str = "temp_downloads",
    target_date: Optional[date] = None,
    report_type: str = "rpp"
) -> Optional[str]:
    """
    RPPトップページに遷移し、最新のレポートをダウンロードする。

    Args:
        page: Playwrightのページオブジェクト
        screenshot_dir (Path): スクリーンショット保存ディレクトリ（オプション）
        download_dir (str): ダウンロード先ディレクトリ
        target_date (Optional[date]): 取得するレポートの日付

    Returns:
        Optional[str]: ダウンロードしたZIPファイルのパス。対象データがなければNone。
    """
    report_info = _resolve_report_type(report_type)
    base_slug = report_info["slug"]

    try:
        # ダウンロードディレクトリの作成
        download_path = Path(download_dir)
        download_path.mkdir(parents=True, exist_ok=True)
        
        # RPPトップページに移動
        logger.info(f"{report_info['label']}トップページに移動します...")
        await page.goto(f"https://ad.rms.rakuten.co.jp/{base_slug}/top", timeout=30000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        await asyncio.sleep(2)
        
        # ページが正しく読み込まれたことを確認
        if not await page.locator('body').is_visible():
            raise Exception("RPPトップページが正しく読み込まれませんでした。")
        
        logger.info(f"{report_info['label']}トップページに正常に移動しました。")
        
        # ナビゲーションメニューの要素をクリック
        logger.info("ナビゲーションメニューから指定の要素をクリックします...")
        nav_selector = '#root > div > div.rpp-header > div:nth-child(2) > nav > div > div.rpp-nav > nav > ul > li:nth-child(6) > a > div'
        
        try:
            # 要素が表示されるまで待機
            await page.locator(nav_selector).wait_for(state="visible", timeout=20000)
            # クリック
            await page.locator(nav_selector).click()
            # ページ遷移を待機
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(3)
            
            logger.info("ナビゲーションメニューの要素をクリックしました。")
            
            # レポートタイプのラジオボタンを選択
            logger.info("レポートタイプを選択します...")
            
            try:
                # レポートタイプのラジオボタンを選択（JavaScriptを使用）
                await page.evaluate('''() => {
                    const radio = document.querySelector('#rdReportTypeItem');
                    if (radio) {
                        radio.click();
                        // フォールバック: クリックイベントを手動で発火
                        radio.dispatchEvent(new Event('change', { bubbles: true }));
                        radio.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    }
                }''')
                await asyncio.sleep(2)
                
                logger.info("レポートタイプを選択しました。")
                
                # 日付の計算
                if target_date:
                    # 指定された日付を使用
                    start_date = target_date
                    end_date = target_date
                else:
                    # 昨日分のみ - 日本時間
                    jst = timezone(timedelta(hours=+9))
                    today = datetime.now(jst).date()
                    end_date = today - timedelta(days=1)  # 昨日
                    start_date = end_date  # 昨日のみ
                
                # 日付を文字列に変換（YYYY-MM-DD形式）
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                logger.info(f"期間を設定します: {start_date_str} から {end_date_str}")
                
                # 開始日の選択
                logger.info("開始日を選択します...")
                await page.get_by_role("textbox", name="Select start").click()
                await page.get_by_role("textbox", name="Select start").fill(start_date_str)
                await page.get_by_role("textbox", name="Select start").press("Enter")
                await asyncio.sleep(1)
                
                # 終了日の選択
                logger.info("終了日を選択します...")
                await page.get_by_role("textbox", name="Select end").click()
                await page.get_by_role("textbox", name="Select end").fill(end_date_str)
                await page.get_by_role("textbox", name="Select end").press("Enter")
                await asyncio.sleep(1)
                
                # 日付の設定を確認
                start_date_value = await page.evaluate('''() => {
                    const element = document.querySelector('input.datepicker-input[placeholder="Select start"]');
                    return element ? element.value : null;
                }''')
                end_date_value = await page.evaluate('''() => {
                    const element = document.querySelector('input.datepicker-input[placeholder="Select end"]');
                    return element ? element.value : null;
                }''')
                logger.info(f"設定後の開始日: {start_date_value}")
                logger.info(f"設定後の終了日: {end_date_value}")
                
                # 日付が正しく設定されているか確認
                if start_date_value != start_date_str or end_date_value != end_date_str:
                    logger.warning("日付が正しく設定されていません。")
                    if screenshot_dir:
                        await page.screenshot(path=screenshot_dir / f"date_not_set_{int(time.time())}.png")
                    raise ValueError("日付の設定に失敗しました。")
                
                logger.info("日付の設定が完了しました。")
                
                # 全商品レポートダウンロードボタンをクリック（JavaScriptを使用）
                download_button_selector = "button:has-text(\"全商品レポートダウンロード\")"
                logger.info("全商品レポートダウンロードボタンをクリックします...")
                try:
                    await page.locator(download_button_selector).click()
                    await asyncio.sleep(1)
                except Exception as click_err:
                    logger.error(f"全商品レポートダウンロードボタンのクリックに失敗しました: {click_err}")
                    raise
                
                logger.info("ダウンロードボタンをクリックしました。")
                
                # ダウンロード履歴をクリック（JavaScriptを使用）
                await page.evaluate('''() => {
                    const historyLink = Array.from(document.querySelectorAll('a')).find(link => link.textContent.includes('ダウンロード履歴'));
                    if (historyLink) {
                        historyLink.click();
                        historyLink.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                    }
                }''')
                await asyncio.sleep(2)
                
                logger.info("ダウンロード履歴をクリックしました。")
                
                # 最新のレポートのステータスが「完了」になるまで待機
                logger.info("レポートのステータスが「完了」になるまで待機します...")
                status_selector = 'table.table tbody tr:first-child td:nth-child(2) div.cell-content'
                max_wait_time = 300  # 最大待機時間（秒）
                check_interval = 5   # チェック間隔（秒）
                elapsed_time = 0
                
                target_row_index = None
                all_rows_no_data = False
                found_no_data_row = False  # 指定日付で「対象データがありません」が見つかったか

                while elapsed_time < max_wait_time and target_row_index is None and not found_no_data_row:
                    try:
                        # 更新ボタンをクリック（JavaScriptを使用）
                        await page.evaluate('''() => {
                            const refreshButton = document.querySelector('#btnDownloadHistoryRefresh');
                            if (refreshButton) {
                                refreshButton.click();
                                refreshButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            }
                        }''')
                        await asyncio.sleep(2)
                        status_text = await page.locator(status_selector).text_content()
                        logger.info(f"最新行のステータス: {status_text.strip() if status_text else 'N/A'}")

                        # 1行目（最新行）のみをチェック（指定日付のレポートは常に1行目に来る）
                        first_row = page.locator('table.table tbody tr:first-child')
                        row_status = (await first_row.locator('td:nth-child(2) div.cell-content').text_content() or "").strip()
                        download_cell = first_row.locator('td:nth-child(3)')
                        download_text = (await download_cell.text_content() or "").strip()
                        
                        logger.info(f"[1行目] ステータス: {row_status}, ダウンロードセル: {download_text}")
                        
                        # ステータスが「完了」の場合
                        if row_status == "完了":
                            # ダウンロードセルの内容を確認
                            if download_text == "対象データがありません":
                                logger.info("1行目のレポートは対象データがありません。")
                                found_no_data_row = True
                                target_row_index = None  # 対象データがないことを示す
                            else:
                                # ダウンロードリンク/ボタンが表示されるまで待機
                                try:
                                    await download_cell.locator('a:has-text("ダウンロード"), button:has-text("ダウンロード")').wait_for(state="visible", timeout=5000)
                                    target_row_index = 0  # 1行目 = インデックス0
                                    logger.info("1行目にダウンロードリンクを検出しました。")
                                except PlaywrightTimeoutError:
                                    logger.info("1行目は完了だがリンク表示を待機中にタイムアウト。再試行します。")
                                    target_row_index = None
                        else:
                            # まだ完了していない
                            target_row_index = None
                    except Exception as e:
                        logger.warning(f"ステータスの確認中にエラーが発生しました: {str(e)}")
                    
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                    logger.info(f"ステータス待機中... {elapsed_time}秒経過")
                
                if target_row_index is None:
                    if found_no_data_row:
                        # 指定日付で「対象データがありません」が見つかった場合
                        logger.info("指定日付のレポートは対象データがありません。")
                        return None
                    elif all_rows_no_data:
                        logger.info("すべての履歴行が『対象データがありません』のため、ダウンロード処理をスキップします。")
                        return None
                    error_msg = "完了状態のダウンロードリンクがタイムアウトまでに見つかりませんでした。"
                    logger.error(error_msg)
                    if screenshot_dir:
                        await page.screenshot(path=screenshot_dir / f"error_status_timeout_{int(time.time())}.png")
                    raise TimeoutError(error_msg)
                
                logger.info(f"ダウンロード対象行: 1行目のリンクをクリックします。")
                download_cell = first_row.locator('td:nth-child(3)')
                download_cell_text = (await download_cell.text_content() or "").strip()
                logger.info(f"ダウンロードセルの内容: {download_cell_text}")
                download_action_locator = download_cell.locator('a:has-text("ダウンロード"), button:has-text("ダウンロード")')
                download_action_count = await download_action_locator.count()
                if download_action_count == 0:
                    logger.warning("完了行にクリック可能な要素が見つかりませんでした。処理をスキップします。")
                    return None
                download_action = download_action_locator.first
                try:
                    action_tag = await download_action.evaluate("node => node.tagName")
                except Exception:
                    action_tag = "UNKNOWN"
                logger.info(f"ダウンロードアクション要素タグ: {action_tag}")

                try:
                    async with page.expect_download() as download_info:
                        await download_action.click()
                        download = await download_info.value
                        logger.info(f"ダウンロードが開始されました: {download.suggested_filename}")

                        # ファイルを保存
                        await download.save_as(download_path / download.suggested_filename)
                        logger.info(f"ファイルを保存しました: {download_path / download.suggested_filename}")

                        return str(download_path / download.suggested_filename)
                except Exception as e:
                    logger.error(f"ダウンロードリンクのクリック中にエラーが発生しました: {str(e)}")
                    if screenshot_dir:
                        await page.screenshot(path=screenshot_dir / f"error_download_link_click_{int(time.time())}.png")
                    raise
            
            except Exception as e:
                logger.error(f"レポートのダウンロード処理に失敗しました: {str(e)}")
                if screenshot_dir:
                    await page.screenshot(path=screenshot_dir / f"error_download_{int(time.time())}.png")
                raise
        
        except Exception as e:
            logger.error(f"ナビゲーションメニューの要素のクリックまたは日付入力に失敗しました: {str(e)}")
            if screenshot_dir:
                await page.screenshot(path=screenshot_dir / f"error_nav_click_{int(time.time())}.png")
            raise
        
    except Exception as e:
        logger.error(f"RPPトップページへの移動中にエラーが発生しました: {str(e)}")
        if screenshot_dir:
            await page.screenshot(path=screenshot_dir / f"error_rpp_top_{int(time.time())}.png")
        raise


async def navigate_to_report_top(
    page,
    screenshot_dir: Optional[Path] = None,
    download_dir: str = "temp_downloads",
    target_date: Optional[date] = None,
    report_type: str = "rpp"
) -> Optional[str]:
    """
    汎用: 指定種別のトップに遷移し、レポートをダウンロードする。
    RPP系以外はセレクタが不明なため、ダウンロード/履歴リンクは
    テキストベースのフォールバックで試行する。
    """
    report_info = _resolve_report_type(report_type)
    base_slug = report_info["slug"]
    top_path = report_info.get("top_path", "top").lstrip("/")
    nav_selector = report_info.get("nav_selector")
    report_radio_selector = report_info.get("report_radio_selector")
    start_placeholder = report_info.get("start_placeholder")
    end_placeholder = report_info.get("end_placeholder")
    download_button_selectors = report_info.get("download_button_selectors") or [
        'button:has-text("全商品レポートダウンロード")',
        'button:has-text("ダウンロード")',
        'a:has-text("ダウンロード")'
    ]
    history_link_text = report_info.get("history_link_text", "ダウンロード履歴")

    download_path = Path(download_dir)
    download_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"{report_info['label']}トップページに移動します...")
    await page.goto(f"https://ad.rms.rakuten.co.jp/{base_slug}/{top_path}", timeout=30000)
    await page.wait_for_load_state('networkidle', timeout=30000)
    await asyncio.sleep(2)

    if not await page.locator('body').is_visible():
        raise Exception(f"{report_info['label']}トップページが正しく読み込まれませんでした。")

    # ナビゲーション（存在する場合のみ）
    if nav_selector:
        try:
            await page.locator(nav_selector).wait_for(state="visible", timeout=20000)
            await page.locator(nav_selector).click()
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"ナビゲーションクリックに失敗しましたが続行します: {str(e)}")

    # レポート種別ラジオ（任意）
    if report_radio_selector:
        try:
            await page.evaluate(f'''() => {{
                const radio = document.querySelector('{report_radio_selector}');
                if (radio) {{
                    radio.click();
                    radio.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    radio.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
                }}
            }}''')
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"レポート種別選択に失敗しましたが続行します: {str(e)}")

    # 日付入力（プレースホルダがある場合のみ）
    if start_placeholder and end_placeholder:
        if target_date:
            start_date = target_date
            end_date = target_date
        else:
            jst = timezone(timedelta(hours=+9))
            today = datetime.now(jst).date()
            end_date = today - timedelta(days=1)
            start_date = end_date
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        try:
            await page.get_by_role("textbox", name=start_placeholder).click()
            await page.get_by_role("textbox", name=start_placeholder).fill(start_date_str)
            await page.get_by_role("textbox", name=start_placeholder).press("Enter")
            await asyncio.sleep(1)
            await page.get_by_role("textbox", name=end_placeholder).click()
            await page.get_by_role("textbox", name=end_placeholder).fill(end_date_str)
            await page.get_by_role("textbox", name=end_placeholder).press("Enter")
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"日付入力に失敗しましたが続行します: {str(e)}")

    # ダウンロード開始
    clicked = False
    for selector in download_button_selectors:
        try:
            await page.locator(selector).click(timeout=5000)
            await asyncio.sleep(1)
            clicked = True
            break
        except Exception:
            continue
    if not clicked:
        logger.warning("ダウンロードボタンをクリックできませんでした。")

    # 履歴ページへ
    try:
        await page.evaluate(f'''() => {{
            const historyLink = Array.from(document.querySelectorAll('a, button')).find(link => link.textContent && link.textContent.includes('{history_link_text}'));
            if (historyLink) {{
                historyLink.click();
                historyLink.dispatchEvent(new MouseEvent('click', {{ bubbles: true }}));
            }}
        }}''')
        await asyncio.sleep(2)
    except Exception as e:
        logger.warning(f"ダウンロード履歴リンクに遷移できませんでしたが続行します: {str(e)}")

    # 完了待ち
    status_selector = 'table.table tbody tr:first-child td:nth-child(2) div.cell-content'
    max_wait_time = 300
    check_interval = 5
    elapsed_time = 0
    target_row_index = None
    found_no_data_row = False

    while elapsed_time < max_wait_time and target_row_index is None and not found_no_data_row:
        try:
            await page.evaluate('''() => {
                const refreshButton = document.querySelector('#btnDownloadHistoryRefresh');
                if (refreshButton) {
                    refreshButton.click();
                    refreshButton.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                }
            }''')
            await asyncio.sleep(2)

            first_row = page.locator('table.table tbody tr:first-child')
            row_status = (await first_row.locator('td:nth-child(2) div.cell-content').text_content() or "").strip()
            download_cell = first_row.locator('td:nth-child(3)')
            download_text = (await download_cell.text_content() or "").strip()

            if row_status == "完了":
                if download_text == "対象データがありません":
                    found_no_data_row = True
                    target_row_index = None
                else:
                    try:
                        await download_cell.locator('a:has-text("ダウンロード"), button:has-text("ダウンロード")').wait_for(state="visible", timeout=5000)
                        target_row_index = 0
                    except PlaywrightTimeoutError:
                        target_row_index = None
            else:
                target_row_index = None
        except Exception as e:
            logger.warning(f"ステータス確認中にエラー: {str(e)}")

        await asyncio.sleep(check_interval)
        elapsed_time += check_interval

    if target_row_index is None:
        if found_no_data_row:
            return None
        raise TimeoutError("完了状態のダウンロードリンクが見つかりませんでした。")

    download_cell = page.locator('table.table tbody tr:first-child td:nth-child(3)')
    download_action_locator = download_cell.locator('a:has-text("ダウンロード"), button:has-text("ダウンロード")')
    if await download_action_locator.count() == 0:
        logger.warning("完了行にクリック可能な要素が見つかりません。")
        return None
    download_action = download_action_locator.first
    async with page.expect_download() as download_info:
        await download_action.click()
        download = await download_info.value
        await download.save_as(download_path / download.suggested_filename)
        return str(download_path / download.suggested_filename)

async def extract_zip_file(zip_file_path: str, extract_dir: str = "temp_downloads", report_slug: str = "rpp") -> str:
    """
    ZIPファイルを展開する
    
    Args:
        zip_file_path (str): ZIPファイルのパス
        extract_dir (str): 展開先ディレクトリ
        
    Returns:
        str: 展開されたCSVファイルのパス
    """
    logger.info(f"ZIPファイルを展開します: {zip_file_path}")
    
    try:
        # 展開先ディレクトリの作成
        extract_path = Path(extract_dir)
        extract_path.mkdir(parents=True, exist_ok=True)
        
        # ZIPファイルを展開
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # 展開されたファイルのパスを取得
        extracted_files = list(extract_path.glob('*.csv'))
        if not extracted_files:
            raise Exception("ZIPファイル内にCSVファイルが見つかりませんでした。")
        
        # 対象レポートのCSVファイルを特定
        target_csv_files = [f for f in extracted_files if report_slug in f.name.lower()]
        if not target_csv_files:
            logger.warning("レポート種別名を含むCSVが見つからなかったため、最初のCSVを使用します。")
            target_csv_files = extracted_files
        
        csv_file_path = str(target_csv_files[0])
        logger.info(f"ZIPファイルを展開しました: {csv_file_path}")
        
        # 元のZIPファイルを削除
        Path(zip_file_path).unlink()
        logger.info(f"元のZIPファイルを削除しました: {zip_file_path}")
        
        return csv_file_path
        
    except Exception as e:
        logger.error(f"ZIPファイルの展開中にエラーが発生しました: {str(e)}")
        raise


async def get_rpp_report_csv(
    rms_credentials: dict,
    rakuten_credentials: dict,
    target_date: Optional[date] = None,
    download_dir: str = "temp_downloads",
    headless: bool = True,
    report_type: str = "rpp"
) -> Optional[str]:
    """
    楽天RMSから指定種別のレポートをダウンロードしてCSVファイルを取得する
    
    Args:
        rms_credentials (dict): RMSの認証情報
        rakuten_credentials (dict): 楽天会員の認証情報
        target_date (Optional[date]): 取得するレポートの日付（指定しない場合は昨日）
        download_dir (str): ダウンロード先ディレクトリ
        headless (bool): ブラウザをヘッドレスモードで実行するかどうか
        report_type (str): 取得するレポート種別（rpp / rpp-exp / rppexp / cpnadv / tda / tdaexp / cpa）
    
    Returns:
        Optional[str]: CSVファイルのパス。取得できない場合はNone。
    """
    report_info = _resolve_report_type(report_type)
    report_slug = report_info["slug"]
    p = await async_playwright().start()
    browser = None
    context = None
    page = None
    
    try:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                '--lang=ja-JP,ja',
                '--no-sandbox',
                '--font-render-hinting=none',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--force-color-profile=srgb',
                '--force-device-scale-factor=1'
            ]
        )
        
        context = await browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            locale='ja-JP'
        )
        
        page = await context.new_page()
        
        # スクリーンショット保存用ディレクトリの作成
        screenshot_dir = Path(download_dir) / "screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # 共通ログイン処理を実行
        await login_to_rms(page, rms_credentials, rakuten_credentials, screenshot_dir)
        
        # 指定種別トップページに遷移しダウンロード
        zip_file_path = await navigate_to_report_top(page, screenshot_dir, download_dir, target_date, report_type=report_type)

        if not zip_file_path:
            logger.info("ダウンロード対象がなかったためZIP展開処理をスキップします。")
            return None
        
        # ZIPファイルを展開
        csv_file_path = await extract_zip_file(zip_file_path, download_dir, report_slug)
        
        return csv_file_path
        
    except Exception as e:
        logger.error(f"RPPレポート取得中にエラーが発生しました: {str(e)}")
        if page and screenshot_dir:
            try:
                await page.screenshot(path=str(screenshot_dir / f"error_{int(time.time())}.png"))
            except Exception:
                pass
        raise
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if p:
            try:
                await p.stop()
            except Exception:
                pass

