"""The session cookie name as a single named constant, shared between the
login endpoint (sets it) and the auth dependency (reads it) - avoids the
name being duplicated as a literal in two places (NFR design)."""

SESSION_COOKIE_NAME = "session_id"
