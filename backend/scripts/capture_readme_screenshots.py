from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs" / "images"
DASHBOARD_URL = "http://127.0.0.1:8000/"


def capture() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-breakpad",
                "--disable-crash-reporter",
                "--disable-features=Crashpad",
            ],
        )
        page = browser.new_page(viewport={"width": 1600, "height": 2200})

        page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)

        page.screenshot(path=str(OUT_DIR / "dashboard-home.png"), full_page=True)

        page.locator("text=Discover + Auto Apply").first.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT_DIR / "discover-auto-apply.png"), full_page=True)

        page.locator("text=Discovered Jobs").first.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT_DIR / "discovered-jobs-selection.png"), full_page=True)

        page.locator("text=Applications").first.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT_DIR / "applications-status.png"), full_page=True)

        browser.close()


if __name__ == "__main__":
    capture()
    print("Saved screenshots to docs/images/")
