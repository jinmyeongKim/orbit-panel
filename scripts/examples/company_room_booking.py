"""Company groupware: open logged in, then run the meeting-room booking steps.

Same pattern as github_login.py — a persistent browser profile keeps the login
session, so after logging in once by hand every later run starts authenticated.

The booking steps inside `book_room()` are a placeholder until they are recorded
for the actual groupware site:

1. Record your own clicks once:
       python -m playwright codegen --channel chrome <company-reservation-URL>
   Log in (if asked) and click through one full room reservation.
   The codegen window shows generated Python lines for every click/fill.
2. Paste those generated lines into `book_room()` below (or hand them to your
   assistant to merge and parameterize).

Orbit Panel item
----------------
- Type = URL, Target = <company reservation page URL>
- Script Type = Python File, Script = scripts/examples/company_room_booking.py
- Run Mode = Script Only

Add the item to a scenario for a one-click routine.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

# ---------------------------------------------------------------------------
# Fill these in for your company's booking routine.
# ---------------------------------------------------------------------------
DEFAULT_TARGET = ""  # e.g. "https://gw.mycompany.com/reservation" (item Target wins if set)
AUTO_BOOK = False    # set True once book_room() contains the real recorded steps
# ---------------------------------------------------------------------------


def profile_dir() -> Path:
    runtime_dir = os.environ.get("ORBIT_PANEL_RUNTIME_DIR")
    base = Path(runtime_dir) if runtime_dir else Path.home() / ".orbit-panel"
    profile = base / "browser_profiles" / "company"
    profile.mkdir(parents=True, exist_ok=True)
    return profile


def book_room(page) -> None:
    """Recorded booking steps go here (from `playwright codegen`).

    Example of what recorded lines look like:
        page.click("text=회의실 예약")
        page.select_option("#room", "대회의실")
        page.fill("#date", "2026-07-06")
        page.click("text=예약하기")
    """
    raise NotImplementedError(
        "Record the booking steps with playwright codegen and paste them here."
    )


def run() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("This script needs Playwright. Run: pip install playwright")
        return 1

    target = (os.environ.get("ORBIT_PANEL_ITEM_TARGET") or DEFAULT_TARGET).strip()
    if not target:
        print("Set the item Target (or DEFAULT_TARGET in this script) to the reservation URL.")
        return 1

    with sync_playwright() as playwright:
        context = None
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
        page.goto(target)
        print(f"Opened {target} with the persistent company profile.")
        print("If a login page appears, log in once by hand - the session is remembered.")

        if AUTO_BOOK:
            try:
                book_room(page)
                print("Booking steps completed.")
            except NotImplementedError as exc:
                print(f"Booking skipped: {exc}")
            except Exception as exc:
                print(f"Booking steps failed: {exc}")
                print("The browser stays open so you can finish by hand.")

        # Keep the script alive until the user closes the browser window.
        try:
            context.wait_for_event("close", timeout=0)
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(run())
