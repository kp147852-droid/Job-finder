from __future__ import annotations

from .models import AdapterRunResult
from .playwright_engine import PlaywrightNotInstalledError, browser_context


class GlassdoorAdapter:
    provider_name = "glassdoor"

    def apply(self, *, user, resume, job, storage_state_path):
        try:
            with browser_context(storage_state_path) as page:
                page.goto(job.apply_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1000)

                apply_btn = page.locator('button:has-text("Easy Apply"), button:has-text("Apply Now")').first
                if apply_btn.count() == 0:
                    return AdapterRunResult(
                        success=False,
                        needs_user_input=True,
                        missing_field="glassdoor_apply_button",
                        prompt="Glassdoor apply entrypoint not found. Start application manually then retry.",
                        details="Apply button unavailable.",
                    )

                apply_btn.click()
                page.wait_for_timeout(900)

                for selector, value in [
                    ('input[type="email"]', user.email),
                    ('input[name*="name"]', user.full_name),
                    ('textarea[name*="cover"]', f"Interested in {job.title} at {job.company}."),
                ]:
                    field = page.locator(selector).first
                    if field.count() > 0 and value:
                        field.fill(value)

                submit = page.locator('button:has-text("Submit"), button:has-text("Apply")').first
                if submit.count() == 0:
                    return AdapterRunResult(
                        success=False,
                        needs_user_input=True,
                        missing_field="glassdoor_custom_questions",
                        prompt="Glassdoor application needs manual answers before submission.",
                        details="Submit control not found.",
                    )

                submit.click()
                return AdapterRunResult(success=True, details="Glassdoor application submitted.")
        except PlaywrightNotInstalledError as exc:
            return AdapterRunResult(success=False, needs_user_input=True, missing_field="playwright", prompt=str(exc), details="Adapter dependency missing.")
        except Exception as exc:
            return AdapterRunResult(success=False, needs_user_input=True, missing_field="glassdoor_runtime", prompt="Glassdoor apply flow encountered an issue and needs manual confirmation.", details=str(exc))
