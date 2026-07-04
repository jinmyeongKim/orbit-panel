from __future__ import annotations

import os
from pathlib import Path
import sys

HELPERS_DIR = Path(__file__).resolve().parents[1]
if str(HELPERS_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_DIR))

from orbit_context import build_logger, load_context


def main() -> None:
    context = load_context()
    logger = build_logger(__file__)
    logger.info("Browser automation started for '%s'", context.title or context.item_id or "unknown item")

    target_url = context.target.strip()
    if not target_url:
        logger.error("No target URL was provided. Use a URL target or set one inside the script.")
        return

    username = os.environ.get("ORBIT_AUTOMATION_USERNAME", "").strip()
    password = os.environ.get("ORBIT_AUTOMATION_PASSWORD", "").strip()
    if not username or not password:
        logger.warning(
            "Credentials are missing. Set ORBIT_AUTOMATION_USERNAME and ORBIT_AUTOMATION_PASSWORD before running."
        )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright is not installed.")
        logger.warning("Install with: pip install playwright")
        logger.warning("Then install browser binaries with: python -m playwright install chromium")
        logger.warning("After that, replace the selector placeholders inside scripts/examples/browser_login_stub.py")
        return

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=False)
        page = browser.new_page()
        page.goto(target_url, wait_until="domcontentloaded")
        logger.info("Opened %s", target_url)

        # Replace the selector placeholders below with the real selectors for your site.
        # page.get_by_label("Email").fill(username)
        # page.get_by_label("Password").fill(password)
        # page.get_by_role("button", name="Log in").click()
        # page.wait_for_load_state("networkidle")

        logger.info("Browser login stub finished. Replace the selector block with the real login steps.")
        browser.close()


if __name__ == "__main__":
    main()
