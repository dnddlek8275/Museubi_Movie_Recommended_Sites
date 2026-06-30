from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models.user import RefreshToken, User
from app.schemas.auth import CreateRefreshToken


def create_refresh_token(db: Session, payload: CreateRefreshToken) -> RefreshToken:
    # auth 로직에서 해시한 Refresh Token 값을 DB에 저장한다.
    if db.get(User, payload.user_id) is None:
        raise ServiceError("사용자를 찾을 수 없습니다.", status_code=404)

    existing_token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == payload.token_hash)
    )
    if existing_token is not None:
        raise ServiceError("이미 저장된 Refresh Token입니다.", status_code=409)

    refresh_token = RefreshToken(
        user_id=payload.user_id,
        token_hash=payload.token_hash,
        expires_at=payload.expires_at,
        user_agent=payload.user_agent,
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def verify_refresh_token(db: Session, token_hash: str) -> RefreshToken:
    # Refresh Token hash를 조회해 만료/폐기 여부를 검증한다.
    refresh_token = get_refresh_token_or_404(db, token_hash)
    now = datetime.now(timezone.utc)

    if refresh_token.revoked_at is not None:
        raise ServiceError("폐기된 Refresh Token입니다.", status_code=401)
    if refresh_token.expires_at <= now:
        raise ServiceError("만료된 Refresh Token입니다.", status_code=401)

    # 재발급 시점을 남겨 토큰 사용 흔적을 DB에서 확인할 수 있게 한다.
    refresh_token.last_used_at = now
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def revoke_refresh_token(db: Session, token_hash: str) -> RefreshToken:
    # Refresh Token을 삭제하지 않고 revoked_at으로 폐기 처리한다.
    refresh_token = get_refresh_token_or_404(db, token_hash)
    if refresh_token.revoked_at is None:
        refresh_token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(refresh_token)
    return refresh_token


def get_refresh_token_or_404(db: Session, token_hash: str) -> RefreshToken:
    # token_hash로 Refresh Token row를 조회하고 없으면 404 예외를 발생시킨다.
    refresh_token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if refresh_token is None:
        raise ServiceError("Refresh Token을 찾을 수 없습니다.", status_code=404)
    return refresh_token
