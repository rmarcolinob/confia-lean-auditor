"""Small local stores. Session cookies contain only an opaque random secret."""
from __future__ import annotations
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import tempfile
import time
from uuid import uuid4

from .models import AuthUser, Role, StoredUser

SCRYPT_N, SCRYPT_R, SCRYPT_P = 1 << 14, 8, 1
PBKDF2_ITERATIONS = 600_000
SESSION_SECONDS = 8 * 60 * 60


def _encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _hash_password(password: str, salt: bytes, kdf: str) -> bytes:
    if kdf == "scrypt":
        if not hasattr(hashlib, "scrypt"):
            raise RuntimeError("scrypt unavailable in this Python runtime")
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R,
                              p=SCRYPT_P, dklen=32, maxmem=32 * 1024 * 1024)
    if kdf == "pbkdf2_sha256":
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt,
                                   PBKDF2_ITERATIONS, dklen=32)
    raise ValueError("unknown password KDF")


class AuthStore:
    def __init__(self, root: Path):
        self.root = root

    @contextmanager
    def _locked(self):
        if self.root.is_symlink():
            raise ValueError("invalid auth directory")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        lock = self.root / ".lock"
        fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _read(self, name: str) -> dict:
        path = self.root / name
        if path.is_symlink():
            raise ValueError("invalid auth file")
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("invalid auth file")
        return data

    def _write(self, name: str, data: dict):
        path = self.root / name
        if path.is_symlink():
            raise ValueError("invalid auth file")
        fd, temporary = tempfile.mkstemp(prefix=".auth-", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                os.fchmod(handle.fileno(), 0o600)
                json.dump(data, handle, ensure_ascii=False, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def create_user(self, *, login: str, display_name: str, role: Role, password: str,
                    tenant_id: str | None = None, classroom_ids: list[str] | None = None) -> AuthUser:
        if not login or not password or not display_name:
            raise ValueError("missing account field")
        salt = secrets.token_bytes(16)
        kdf = "scrypt" if hasattr(hashlib, "scrypt") else "pbkdf2_sha256"
        password_hash = _hash_password(password, salt, kdf)
        user = StoredUser(user_id=f"usr_{uuid4().hex}", login=login, display_name=display_name,
                          role=role, tenant_id=tenant_id, classroom_ids=classroom_ids or [],
                          password_salt=_encode(salt), password_hash=_encode(password_hash),
                          password_kdf=kdf,
                          scrypt_n=SCRYPT_N if kdf == "scrypt" else None,
                          scrypt_r=SCRYPT_R if kdf == "scrypt" else None,
                          scrypt_p=SCRYPT_P if kdf == "scrypt" else None,
                          pbkdf2_iterations=PBKDF2_ITERATIONS if kdf == "pbkdf2_sha256" else None)
        with self._locked():
            users = self._read("users.json")
            if login in users:
                raise ValueError("account already exists")
            users[login] = user.model_dump(mode="json")
            self._write("users.json", users)
        return user.public()

    def get_user(self, user_id: str) -> AuthUser | None:
        with self._locked():
            for value in self._read("users.json").values():
                user = StoredUser.model_validate(value)
                if user.user_id == user_id:
                    return user.public()
        return None

    def authenticate(self, login: str, password: str) -> AuthUser | None:
        with self._locked():
            raw = self._read("users.json").get(login)
        if raw is None:
            # Do comparable work without disclosing whether the login exists.
            _hash_password(password, b"\0" * 16,
                           "scrypt" if hasattr(hashlib, "scrypt") else "pbkdf2_sha256")
            return None
        user = StoredUser.model_validate(raw)
        if user.password_kdf == "scrypt" and (user.scrypt_n, user.scrypt_r, user.scrypt_p) != (
                SCRYPT_N, SCRYPT_R, SCRYPT_P):
            return None
        if user.password_kdf == "pbkdf2_sha256" and user.pbkdf2_iterations != PBKDF2_ITERATIONS:
            return None
        expected = base64.b64decode(user.password_hash, validate=True)
        candidate = _hash_password(password, base64.b64decode(user.password_salt, validate=True),
                                   user.password_kdf)
        return user.public() if user.active and hmac.compare_digest(candidate, expected) else None

    def create_session(self, user_id: str, lifetime=SESSION_SECONDS) -> str:
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode("ascii")).hexdigest()
        with self._locked():
            sessions = self._read("sessions.json")
            now = int(time.time())
            sessions = {key: value for key, value in sessions.items() if value["expires_at"] > now}
            sessions[digest] = {"user_id": user_id, "expires_at": now + lifetime}
            self._write("sessions.json", sessions)
        return token

    def session_user(self, token: str | None) -> AuthUser | None:
        if not token or len(token) > 128:
            return None
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self._locked():
            session = self._read("sessions.json").get(digest)
        if not session or session["expires_at"] <= int(time.time()):
            return None
        user = self.get_user(session["user_id"])
        return user if user and user.active else None

    def revoke_session(self, token: str | None):
        if not token:
            return
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self._locked():
            sessions = self._read("sessions.json")
            sessions.pop(digest, None)
            self._write("sessions.json", sessions)
