from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateRefreshToken(BaseModel):
    user_id: int
    token_hash: str
    expires_at: datetime
    user_agent: str | None = None


class VerifyRefreshToken(BaseModel):
    token_hash: str


class RevokeRefreshToken(BaseModel):
    token_hash: str


class CreateEmailVerificationCode(BaseModel):
    email: str
    code_hash: str
    expires_at: datetime
    purpose: str = "signup"


class VerifyEmailVerificationCode(BaseModel):
    email: str
    code_hash: str
    purpose: str = "signup"


class ReadEmailVerificationCode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    purpose: str
    code_hash: str
    created_at: datetime
    expires_at: datetime
    verified_at: datetime | None
    attempt_count: int


class CreatePasswordResetToken(BaseModel):
    email: str
    token_hash: str
    expires_at: datetime


class VerifyPasswordResetToken(BaseModel):
    token_hash: str


class ResetPasswordWithToken(BaseModel):
    token_hash: str
    new_password_hash: str


class ReadPasswordResetToken(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int
    token_hash: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None


class PasswordResetVerifyResult(BaseModel):
    user_id: int
    token_id: UUID


class ReadRefreshToken(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: int
    token_hash: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    last_used_at: datetime | None
    user_agent: str | None


class RefreshTokenVerifyResult(BaseModel):
    user_id: int
    token_id: UUID
