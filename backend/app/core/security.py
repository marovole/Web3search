"""Minimal security helpers for JWT-style bearer auth.

This implementation is intentionally lightweight to unblock API startup. For
production, replace with a hardened auth service and key rotation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import jwt

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token and return its payload, or ``None`` on failure."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception as exc:  # noqa: BLE001 - we want to log any auth failure
        logger.warning("Token verification failed: %s", exc)
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    payload = verify_token(token)
    if not payload:
        return None
    return payload.get("user_id") or payload.get("sub")


def issue_dev_token(user_id: str) -> str:
    """Issue a minimal JWT for local development and tests."""
    return jwt.encode({"sub": user_id}, JWT_SECRET, algorithm=JWT_ALGORITHM)
