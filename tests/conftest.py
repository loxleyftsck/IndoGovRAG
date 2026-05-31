import pytest

@pytest.fixture(autouse=True)
def clear_rate_limiter():
    from api.security import rate_limiter
    rate_limiter._ip_windows.clear()
    rate_limiter._user_windows.clear()
    rate_limiter._api_key_windows.clear()
    rate_limiter._ip_bursts.clear()
    rate_limiter._rate_limit_hits.clear()
    from api.rate_limiter import _ABUSE_STORE, _ABUSE_LOCK
    with _ABUSE_LOCK:
        _ABUSE_STORE.clear()
