from __future__ import annotations

from .models import AdapterRunResult
from .playwright_engine import PlaywrightNotInstalledError, browser_context


class LinkedInAdapter:
    provider_name = "linkedin"

    def apply(self, *, user, resume, job, storage_state_path):
        try:
            with browser_context(storage_state_path) as page:
                page.goto(job.apply_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1000)

                easy_apply = page.locator('button:has-text("Easy Apply")').first
                if easy_apply.count() == 0:
                    return AdapterRunResult(
                        success=False,
                        needs_user_input=True,
                        missing_field="apply_entrypoint",
                        prompt="Easy Apply button not found. Log in and start the application manually, then retry.",
                        details="LinkedIn Easy Apply was unavailable on this posting.",
                    )

                easy_apply.click()
                page.wait_for_timeout(1200)

                for selector, value in [
                    ('input[name="email"]', user.email),
                    ('input[name="firstName"]', user.full_name.split(" ")[0]),
                    ('input[name="lastName"]', " ".join(user.full_name.split(" ")[1:]) or user.full_name.split(" ")[0]),
                    ('textarea[aria-label*="Cover letter"]', f"I am interested in the {job.title} role."),
                ]:
                    field = page.locator(selector).first
                    if field.count() > 0 and value:
                        field.fill(value)

                submit = page.locator('button:has-text("Submit application")').first
                if submit.count() == 0:
                    return AdapterRunResult(
                        success=False,
                        needs_user_input=True,
                        missing_field="linkedin_custom_questions",
                        prompt="LinkedIn has additional questions that require your review.",
                        details="Submit button was not available after autofill.",
                    )

                submit.click()
                return AdapterRunResult(success=True, details="LinkedIn application submitted.")
        except PlaywrightNotInstalledError as exc:
            return AdapterRunResult(success=False, needs_user_input=True, missing_field="playwright", prompt=str(exc), details="Adapter dependency missing.")
        except Exception as exc:
            return AdapterRunResult(success=False, needs_user_input=True, missing_field="linkedin_runtime", prompt="LinkedIn apply flow encountered an issue and needs manual confirmation.", details=str(exc))
