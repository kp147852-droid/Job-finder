from __future__ import annotations

import json
import os

from cryptography.fernet import Fernet

from .storage import VAULT_CREDENTIALS


def _get_fernet() -> Fernet:
    key = os.getenv("VAULT_FERNET_KEY")
    if not key:
        # Dev fallback only; set VAULT_FERNET_KEY in production.
        key = Fernet.generate_key().decode("utf-8")
    return Fernet(key.encode("utf-8"))


def save_credential(user_id: str, provider: str, data: dict) -> None:
    cipher = _get_fernet()
    payload = json.dumps(data).encode("utf-8")
    encrypted = cipher.encrypt(payload).decode("utf-8")
    VAULT_CREDENTIALS[(user_id, provider.lower())] = encrypted


def has_credential(user_id: str, provider: str) -> bool:
    return (user_id, provider.lower()) in VAULT_CREDENTIALS
