from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    SCHOOL_MANAGER = "SCHOOL_MANAGER"
    NETWORK_MANAGER = "NETWORK_MANAGER"
    ADMIN = "ADMIN"


class AuthModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AuthUser(AuthModel):
    user_id: str
    login: str
    display_name: str
    role: Role
    tenant_id: Optional[str] = None
    classroom_ids: list[str] = Field(default_factory=list)
    active: bool = True


class StoredUser(AuthUser):
    password_salt: str
    password_hash: str
    password_kdf: Literal["scrypt", "pbkdf2_sha256"] = "scrypt"
    scrypt_n: Optional[int] = None
    scrypt_r: Optional[int] = None
    scrypt_p: Optional[int] = None
    pbkdf2_iterations: Optional[int] = None

    def public(self) -> AuthUser:
        return AuthUser.model_validate(self.model_dump(include=set(AuthUser.model_fields)))


class LoginRequest(AuthModel):
    login: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=1024)
