"""Password hashing (scrypt, stdlib) and a simple login throttle."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from collections import defaultdict

_N, _R, _P = 2**14, 8, 1
MIN_PASSWORD_LENGTH = 12


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"A jelszó legalább {MIN_PASSWORD_LENGTH} karakter legyen.")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return "scrypt${}${}".format(base64.b64encode(salt).decode(), base64.b64encode(digest).decode())


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    salt, expected = base64.b64decode(salt_b64), base64.b64decode(digest_b64)
    actual = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=len(expected))
    return hmac.compare_digest(actual, expected)


# A hash to verify against when the user doesn't exist, so the response time
# doesn't reveal which e-mail addresses have accounts.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


class LoginThrottle:
    """Locks an e-mail address after repeated failures. In memory: resets on restart."""

    def __init__(self, max_failures: int = 5, window_seconds: int = 900) -> None:
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, list[float]] = defaultdict(list)

    def _recent(self, key: str) -> list[float]:
        cutoff = time.monotonic() - self.window
        self._failures[key] = [t for t in self._failures[key] if t > cutoff]
        return self._failures[key]

    def blocked(self, email: str) -> bool:
        return len(self._recent(email.lower())) >= self.max_failures

    def fail(self, email: str) -> None:
        self._recent(email.lower()).append(time.monotonic())

    def reset(self, email: str) -> None:
        self._failures.pop(email.lower(), None)
