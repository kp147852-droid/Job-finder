from __future__ import annotations

from contextlib import contextmanager

from ..config import settings

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None
    PlaywrightTimeoutError = Exception


class PlaywrightNotInstalledError(RuntimeError):
    pass


@contextmanager
def browser_context(storage_state_path: str | None):
    if sync_playwright is None:
        raise PlaywrightNotInstalledError(
            "Playwright is not installed. Install with `pip install playwright` and `playwright install`"
        )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=settings.playwright_headless)
        context = browser.new_context(storage_state=storage_state_path) if storage_state_path else browser.new_context()
        page = context.new_page()
        try:
            yield page
        finally:
            context.close()
            browser.close()
