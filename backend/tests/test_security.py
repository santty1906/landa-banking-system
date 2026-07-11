from app.security import hash_password, verify_password


def test_hash_password_returns_string():
    h = hash_password("hello")
    assert isinstance(h, str)
    assert len(h) > 0


def test_verify_correct_password():
    h = hash_password("correct-password")
    assert verify_password("correct-password", h) is True


def test_verify_wrong_password():
    h = hash_password("correct-password")
    assert verify_password("wrong-password", h) is False


def test_different_hashes_for_same_password():
    h1 = hash_password("samepass")
    h2 = hash_password("samepass")
    assert h1 != h2


def test_empty_password():
    h = hash_password("")
    assert verify_password("", h) is True
    assert verify_password("notempty", h) is False


def test_password_with_special_chars():
    pwd = "p@$$w0rd!#$"
    h = hash_password(pwd)
    assert verify_password(pwd, h) is True

def test_hash_device_token_consistent():
    from app.security import _hash_device_token
    assert _hash_device_token("abc") == _hash_device_token("abc")


def test_hash_device_token_differs():
    from app.security import _hash_device_token
    assert _hash_device_token("abc") != _hash_device_token("xyz")


def test_is_trusted_device_no_cookie(app):
    with app.test_request_context("/"):
        from app.security import is_trusted_device
        assert is_trusted_device(999) is False

