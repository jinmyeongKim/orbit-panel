from __future__ import annotations

import os
from pathlib import Path
import sys

HELPERS_DIR = Path(__file__).resolve().parents[1]
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from orbit_context import build_logger, load_context


NAVER_HOME_URL = "https://www.naver.com/"
NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _load_credentials() -> tuple[str, str]:
    username = (
        os.environ.get("ORBIT_NAVER_ID")
        or os.environ.get("NAVER_ID")
        or os.environ.get("ORBIT_AUTOMATION_USERNAME")
        or ""
    ).strip()
    password = (
        os.environ.get("ORBIT_NAVER_PASSWORD")
        or os.environ.get("NAVER_PASSWORD")
        or os.environ.get("ORBIT_AUTOMATION_PASSWORD")
        or ""
    ).strip()
    return username, password


def main() -> None:
    context = load_context()
    logger = build_logger(__file__)

    username, password = _load_credentials()
    target_url = context.target.strip() or NAVER_HOME_URL
    keep_open = _env_bool("ORBIT_NAVER_KEEP_OPEN", default=True)

    logger.info("Naver automation started for '%s'", context.title or context.item_id or "unknown item")
    logger.info("Configured target URL: %s", target_url)

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright is not installed.")
        logger.warning("Install with: pip install playwright")
        logger.warning("Then install browser binaries with: python -m playwright install chromium")
        return

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page()

        if username and password:
            logger.info("Credentials found. Opening the Naver login page.")
            page.goto(NAVER_LOGIN_URL, wait_until="domcontentloaded")
            page.locator("#id").fill(username)
            page.locator("#pw").fill(password)
            page.locator("#log\\.login").click()

            try:
                page.wait_for_url("**/www.naver.com/**", timeout=15000)
                logger.info("Login flow appears to have reached the Naver home page.")
            except PlaywrightTimeoutError:
                logger.warning(
                    "Login did not automatically reach the expected home page. "
                    "Additional verification such as CAPTCHA or 2FA may be required."
                )
        else:
            logger.info("Credentials were not provided. Opening the target URL without login automation.")
            page.goto(target_url, wait_until="domcontentloaded")

        current_url = page.url
        if target_url and current_url.rstrip("/") != target_url.rstrip("/"):
            try:
                page.goto(target_url, wait_until="domcontentloaded")
                logger.info("Moved to the final target URL: %s", target_url)
            except PlaywrightTimeoutError:
                logger.warning("The final target URL did not finish loading within the timeout: %s", target_url)

        if not keep_open:
            logger.info("Closing the browser automatically because ORBIT_NAVER_KEEP_OPEN=false.")
            browser.close()
            return

        logger.info("Keeping the browser open until you close it manually.")
        try:
            while not page.is_closed():
                page.wait_for_timeout(1000)
        except KeyboardInterrupt:
            logger.info("Browser wait interrupted from the console.")

        browser.close()


if __name__ == "__main__":
    main()
