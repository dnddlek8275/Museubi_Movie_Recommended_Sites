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
