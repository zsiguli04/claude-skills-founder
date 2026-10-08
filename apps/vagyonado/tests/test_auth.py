import pytest

from vagyonado_app.auth import LoginThrottle, hash_password, verify_password


def test_hash_and_verify():
    h = hash_password("a long enough password")
    assert h.startswith("scrypt$")
    assert verify_password("a long enough password", h)
    assert not verify_password("wrong password here", h)
    assert h != hash_password("a long enough password")  # salted


def test_short_password_rejected():
    with pytest.raises(ValueError):
        hash_password("short")


def test_garbage_hash_never_verifies():
    assert not verify_password("anything", "not-a-hash")


def test_throttle():
    t = LoginThrottle(max_failures=3)
    for _ in range(3):
        assert not t.blocked("A@b.hu")
        t.fail("a@b.hu")
    assert t.blocked("a@B.hu")
    t.reset("a@b.hu")
    assert not t.blocked("a@b.hu")
