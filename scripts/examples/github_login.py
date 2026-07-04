"""Open GitHub already logged in, using a persistent Orbit Panel browser profile.

How it works
------------
1. Launches Chrome (or Edge/Chromium) with a dedicated profile stored under the
   Orbit Panel runtime directory, separate from your everyday browser.
2. If the profile already holds a GitHub session, the page simply opens logged in.
3. If the session expired and credentials are stored in Windows Credential Manager,
   the login form (and a TOTP 2FA code, when a secret is stored) is filled automatically.
4. Otherwise the login page is left open — log in once by hand and the session is
   remembered for every later run.

Setup
-----
Required:   pip install playwright
Optional (credential autofill):   pip install keyring pyotp
                                  python scripts/examples/github_login.py --setup

Orbit Panel item
----------------
- Type = URL, Target = https://github.com  (or any GitHub page you want to land on)
- Script Type = Python File, Script = scripts/examples/github_login.py
- Run Mode = Script Only

Add the item to a scenario to make it part of a one-click routine.

Security notes
--------------
- Credentials are stored per-user in Windows Credential Manager (DPAPI), never in files.
- Storing the TOTP secret is optional: without it you confirm 2FA by hand only when
  the saved session expires, which GitHub keeps alive for a long time anyway.
"""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path
import sys

LOGIN_URL = "https://github.com/login"
DEFAULT_TARGET = "https://github.com"
KEYRING_SERVICE = "orbit-panel-github"


def profile_dir() -> Path:
    runtime_dir = os.environ.get("ORBIT_PANEL_RUNTIME_DIR")
    base = Path(runtime_dir) if runtime_dir else Path.home() / ".orbit-panel"
    profile = base / "browser_profiles" / "github"
    profile.mkdir(parents=True, exist_ok=True)
    return profile


def get_secret(name: str) -> str | None:
    try:
        import keyring
    except ImportError:
        return None

    try:
        return keyring.get_password(KEYRING_SERVICE, name)
    except Exception:
        return None


def totp_code() -> str | None:
    secret = get_secret("totp-secret")
    if not secret:
        return None

    try:
        import pyotp
    except ImportError:
        print("A TOTP secret is stored but pyotp is missing. Run: pip install pyotp")
        return None

    return pyotp.TOTP(secret.replace(" ", "")).now()


def run_setup() -> int:
    try:
        import keyring
    except ImportError:
        print("Credential storage needs the keyring package. Run: pip install keyring")
        return 1

    print("Credentials are saved to Windows Credential Manager for the current user.")
    username = input("GitHub username or email: ").strip()
    password = getpass.getpass("GitHub password: ")
    totp_secret = input("TOTP 2FA secret (optional, Enter to skip): ").strip()

    if not username or not password:
        print("Username and password are required. Nothing was saved.")
        return 1

    keyring.set_password(KEYRING_SERVICE, "username", username)
    keyring.set_password(KEYRING_SERVICE, "password", password)
    if totp_secret:
        keyring.set_password(KEYRING_SERVICE, "totp-secret", totp_secret)

    print("Saved. Delete later via Windows Credential Manager (service: orbit-panel-github).")
    return 0


def is_logged_in(context) -> bool:
    for cookie in context.cookies("https://github.com"):
        if cookie["name"] == "logged_in" and cookie["value"] == "yes":
            return True
    return False


def try_credential_login(page) -> None:
    username = get_secret("username")
    password = get_secret("password")

    page.goto(LOGIN_URL)

    if not username or not password:
        print(
            "No stored credentials. Log in once by hand — the session is saved in the "
            "Orbit Panel profile, so later runs open GitHub already logged in.\n"
            "To store credentials for autofill: python scripts/examples/github_login.py --setup"
        )
        return

    page.fill("#login_field", username)
    page.fill("#password", password)
    page.click("input[name='commit']")

    try:
        page.wait_for_url("**/sessions/two-factor**", timeout=8000)
    except Exception:
        return  # No 2FA challenge — either logged in or an error page the user can see.

    code = totp_code()
    if code:
        # GitHub auto-submits once six digits are entered.
        page.fill("#app_totp", code)
        print("Filled the TOTP code automatically.")
    else:
        print("Confirm the 2FA challenge by hand; the session is remembered afterwards.")


def run() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("This script needs Playwright. Run: pip install playwright")
        return 1

    target = os.environ.get("ORBIT_PANEL_ITEM_TARGET") or DEFAULT_TARGET
    if "github.com" not in target:
        target = DEFAULT_TARGET

    with sync_playwright() as playwright:
        context = None
        # Reuse an installed browser so `playwright install` is unnecessary.
        for channel in ("chrome", "msedge", None):
            try:
                context = playwright.chromium.launch_persistent_context(
                    str(profile_dir()),
                    headless=False,
                    channel=channel,
                    no_viewport=True,
                    args=["--start-maximized"],
                )
                break
            except Exception:
                continue

        if context is None:
            print("No Chromium-based browser found. Run: playwright install chromium")
            return 1

        page = context.pages[0] if context.pages else context.new_page()

        if is_logged_in(context):
            print("GitHub session found. Opening logged in.")
            page.goto(target)
        else:
            try_credential_login(page)
            if is_logged_in(context):
                page.goto(target)

        # Keep the script alive until the user closes the browser window.
        try:
            context.wait_for_event("close", timeout=0)
        except Exception:
            pass

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Store GitHub credentials in Windows Credential Manager for autofill.",
    )
    args = parser.parse_args()

    if args.setup:
        return run_setup()
    return run()


if __name__ == "__main__":
    sys.exit(main())
