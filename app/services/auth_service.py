from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models.user import EmailVerificationCode, PasswordResetToken, RefreshToken, User
from app.schemas.auth import CreateEmailVerificationCode, CreatePasswordResetToken, CreateRefreshToken


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


def create_email_verification_code(
    db: Session,
    payload: CreateEmailVerificationCode,
) -> EmailVerificationCode:
    # B1이 이메일로 보낼 인증 코드의 hash를 회원가입 전 email 기준으로 저장한다.
    verification_code = EmailVerificationCode(
        email=payload.email,
        purpose=payload.purpose,
        code_hash=payload.code_hash,
        expires_at=payload.expires_at,
    )
    db.add(verification_code)
    db.commit()
    db.refresh(verification_code)
    return verification_code


def verify_email_verification_code(
    db: Session,
    *,
    email: str,
    code_hash: str,
    purpose: str = "signup",
    max_attempts: int = 5,
) -> EmailVerificationCode:
    # 최신 미인증 코드를 기준으로 만료/시도횟수/code_hash를 검증하고 인증 완료 처리한다.
    verification_code = get_latest_email_verification_code_or_404(
        db,
        email=email,
        purpose=purpose,
    )
    now = datetime.now(timezone.utc)

    if verification_code.expires_at <= now:
        raise ServiceError("만료된 이메일 인증 코드입니다.", status_code=401)
    if verification_code.attempt_count >= max_attempts:
        raise ServiceError("이메일 인증 코드 입력 횟수를 초과했습니다.", status_code=429)
    if verification_code.code_hash != code_hash:
        verification_code.attempt_count += 1
        db.commit()
        raise ServiceError("이메일 인증 코드가 일치하지 않습니다.", status_code=401)

    verification_code.verified_at = now
    db.commit()
    db.refresh(verification_code)
    return verification_code


def get_latest_email_verification_code_or_404(
    db: Session,
    *,
    email: str,
    purpose: str = "signup",
) -> EmailVerificationCode:
    # 같은 이메일로 여러 코드가 발급될 수 있으므로 가장 최근 미인증 코드만 검증 대상으로 삼는다.
    verification_code = db.scalar(
        select(EmailVerificationCode)
        .where(
            EmailVerificationCode.email == email,
            EmailVerificationCode.purpose == purpose,
            EmailVerificationCode.verified_at.is_(None),
        )
        .order_by(desc(EmailVerificationCode.created_at))
    )
    if verification_code is None:
        raise ServiceError("이메일 인증 코드를 찾을 수 없습니다.", status_code=404)
    return verification_code


def create_password_reset_token(db: Session, payload: CreatePasswordResetToken) -> PasswordResetToken:
    # B1이 이메일로 보낼 1회용 재설정 토큰의 hash만 DB에 저장한다.
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        raise ServiceError("사용자를 찾을 수 없습니다.", status_code=404)

    existing_token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == payload.token_hash)
    )
    if existing_token is not None:
        raise ServiceError("이미 저장된 비밀번호 재설정 토큰입니다.", status_code=409)

    password_reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=payload.token_hash,
        expires_at=payload.expires_at,
    )
    db.add(password_reset_token)
    db.commit()
    db.refresh(password_reset_token)
    return password_reset_token


def verify_password_reset_token(db: Session, token_hash: str) -> PasswordResetToken:
    # 비밀번호 재설정 토큰 hash를 조회해 만료/사용 완료 여부를 검증한다.
    password_reset_token = get_password_reset_token_or_404(db, token_hash)
    now = datetime.now(timezone.utc)

    if password_reset_token.used_at is not None:
        raise ServiceError("이미 사용된 비밀번호 재설정 토큰입니다.", status_code=401)
    if password_reset_token.revoked_at is not None:
        raise ServiceError("폐기된 비밀번호 재설정 토큰입니다.", status_code=401)
    if password_reset_token.expires_at <= now:
        raise ServiceError("만료된 비밀번호 재설정 토큰입니다.", status_code=401)

    return password_reset_token


def reset_password_with_token(db: Session, token_hash: str, new_password_hash: str) -> User:
    # 검증된 1회용 토큰으로 사용자 비밀번호 hash를 변경하고 토큰을 사용 완료 처리한다.
    password_reset_token = verify_password_reset_token(db, token_hash)
    user = db.get(User, password_reset_token.user_id)
    if user is None:
        raise ServiceError("사용자를 찾을 수 없습니다.", status_code=404)

    user.password_hash = new_password_hash
    password_reset_token.used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def revoke_password_reset_token(db: Session, token_hash: str) -> PasswordResetToken:
    # 비밀번호 변경에 쓰지 않은 재설정 토큰을 강제로 폐기 처리한다.
    password_reset_token = get_password_reset_token_or_404(db, token_hash)
    if password_reset_token.revoked_at is None:
        password_reset_token.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(password_reset_token)
    return password_reset_token


def get_password_reset_token_or_404(db: Session, token_hash: str) -> PasswordResetToken:
    # token_hash로 비밀번호 재설정 토큰 row를 조회하고 없으면 404 예외를 발생시킨다.
    password_reset_token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    if password_reset_token is None:
        raise ServiceError("비밀번호 재설정 토큰을 찾을 수 없습니다.", status_code=404)
    return password_reset_token
