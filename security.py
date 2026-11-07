"""Web security helpers: CSRF protection, login throttling, HTTP headers."""
import hmac
import secrets
from datetime import datetime, timedelta

from flask import abort, request, session

# ---------------------------------------------------------------- CSRF -----

CSRF_SESSION_KEY = "_csrf_token"


def get_csrf_token() -> str:
    """Return the per-session CSRF token, creating it on first use."""
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def check_csrf() -> None:
    """Reject state-changing requests that do not carry the session's token.

    The token is accepted from a ``csrf_token`` form field (HTML forms) or an
    ``X-CSRFToken`` header (fetch calls from dashboard.js).
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    expected = session.get(CSRF_SESSION_KEY)
    sent = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
    if not expected or not sent or not hmac.compare_digest(expected, sent):
        abort(400, description="Jeton CSRF invalide ou manquant.")


# ------------------------------------------------------ login throttling ---

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW = timedelta(minutes=15)


def _window_start() -> str:
    return (datetime.now() - LOCKOUT_WINDOW).isoformat()


def is_locked_out(db, username: str, ip: str) -> bool:
    """True when this username *or* this IP has too many recent failures."""
    row = db.execute(
        "SELECT "
        " SUM(CASE WHEN username = ? THEN 1 ELSE 0 END) AS by_user, "
        " SUM(CASE WHEN ip = ? THEN 1 ELSE 0 END) AS by_ip "
        "FROM login_attempts WHERE timestamp > ?",
        (username, ip, _window_start()),
    ).fetchone()
    by_user = row["by_user"] or 0
    by_ip = row["by_ip"] or 0
    return by_user >= MAX_FAILED_ATTEMPTS or by_ip >= MAX_FAILED_ATTEMPTS * 4


def record_failed_login(db, username: str, ip: str) -> None:
    db.execute(
        "INSERT INTO login_attempts (username, ip, timestamp) VALUES (?, ?, ?)",
        (username, ip, datetime.now().isoformat()),
    )
    db.commit()


def clear_failed_logins(db, username: str) -> None:
    db.execute("DELETE FROM login_attempts WHERE username = ?", (username,))
    db.commit()


# ------------------------------------------------------- password policy ---

def password_problems(password: str) -> list[str]:
    """Return a list of human-readable reasons the password is too weak."""
    problems = []
    if len(password) < 8:
        problems.append("au moins 8 caractères")
    if not any(c.isdigit() for c in password):
        problems.append("au moins un chiffre")
    if not any(c.isalpha() for c in password):
        problems.append("au moins une lettre")
    return problems


# ------------------------------------------------------------- headers -----

CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
    "font-src 'self' https://cdnjs.cloudflare.com; "
    "img-src 'self' data:; "
    "frame-ancestors 'none'; "
    "form-action 'self'"
)


def add_security_headers(response):
    response.headers.setdefault("Content-Security-Policy", CSP)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    return response
