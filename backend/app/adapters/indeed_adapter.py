from __future__ import annotations

from .models import AdapterRunResult
from .playwright_engine import PlaywrightNotInstalledError, browser_context


class IndeedAdapter:
    provider_name = "indeed"

    def apply(self, *, user, resume, job, storage_state_path):
        try:
            with browser_context(storage_state_path) as page:
                page.goto(job.apply_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1000)

                apply_btn = page.locator('button:has-text("Apply")').first
                if apply_btn.count() == 0:
                    return AdapterRunResult(
                        success=False,
                        needs_user_input=True,
                        missing_field="indeed_apply_button",
                        prompt="Apply button not found. Confirm login/session and open application manually.",
                        details="Indeed apply entrypoint missing.",
                    )

                apply_btn.click()
                page.wait_for_timeout(900)

                for selector, value in [
                    ('input[type="email"]', user.email),
                    ('input[name*="name"]', user.full_name),
                    ('input[type="tel"]', ""),
                ]:
                    field = page.locator(selector).first
                    if field.count() > 0 and value:
                        field.fill(value)

                resume_upload = page.locator('input[type="file"]').first
                if resume_upload.count() > 0:
                    return AdapterRunResult(
                        success=False,
                        needs_user_input=True,
                        missing_field="resume_file_upload",
                        prompt="Indeed requires a resume file upload in this flow. Upload your file and continue.",
                        details="File picker detected.",
                    )

                submit = page.locator('button:has-text("Submit")').first
                if submit.count() == 0:
                    return AdapterRunResult(
                        success=False,
                        needs_user_input=True,
                        missing_field="indeed_custom_questions",
                        prompt="Indeed has custom questions requiring manual input.",
                        details="Submit button unavailable after autofill.",
                    )

                submit.click()
                return AdapterRunResult(success=True, details="Indeed application submitted.")
        except PlaywrightNotInstalledError as exc:
            return AdapterRunResult(success=False, needs_user_input=True, missing_field="playwright", prompt=str(exc), details="Adapter dependency missing.")
        except Exception as exc:
            return AdapterRunResult(success=False, needs_user_input=True, missing_field="indeed_runtime", prompt="Indeed apply flow encountered an issue and needs manual confirmation.", details=str(exc))
