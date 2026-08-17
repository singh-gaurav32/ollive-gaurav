"""The session cookie name as a single named constant, shared between the
login endpoint (sets it) and the auth dependency (reads it) - avoids the
name being duplicated as a literal in two places (NFR design)."""

import os

SESSION_COOKIE_NAME = "session_id"


def session_cookie_is_secure() -> bool:
    """Whether the session cookie should carry the Secure attribute (HTTPS
    only). Defaults to True (fail toward the safer behavior) - every real
    deployment of this app is HTTPS (k3s + cert-manager), so nothing needs
    to opt in. Local dev/docker-compose, which run over plain HTTP, opt out
    via SESSION_COOKIE_SECURE=false - without it the browser would silently
    refuse to store the cookie at all, breaking login. Read live (not
    cached at import time) so tests can override it with monkeypatch."""
    return os.environ.get("SESSION_COOKIE_SECURE", "true").strip().lower() not in ("false", "0", "no")
