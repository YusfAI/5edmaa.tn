"""
Shared rate limiter instance.

Split into its own module (rather than defined in main.py) so route modules
like auth.py can import it without a circular import back to main.py.

Note: this uses slowapi's default in-memory store, which is per-process —
fine for a single-instance deployment, but limits won't be shared across
multiple worker processes/replicas. Point it at Redis (storage_uri=...) if
this is ever deployed with more than one process.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings

limiter = Limiter(key_func=get_remote_address, enabled=settings.rate_limit_enabled)
