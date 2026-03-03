from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AdapterRunResult:
    success: bool
    needs_user_input: bool = False
    missing_field: str | None = None
    prompt: str | None = None
    details: str | None = None
