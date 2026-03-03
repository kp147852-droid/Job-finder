from __future__ import annotations

from .glassdoor_adapter import GlassdoorAdapter
from .indeed_adapter import IndeedAdapter
from .linkedin_adapter import LinkedInAdapter


def get_adapter(provider: str):
    registry = {
        "linkedin": LinkedInAdapter(),
        "indeed": IndeedAdapter(),
        "glassdoor": GlassdoorAdapter(),
    }
    adapter = registry.get(provider.lower())
    if not adapter:
        raise ValueError(f"Unsupported adapter provider: {provider}")
    return adapter
