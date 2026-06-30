# CineVerse DB/Service Module

이 폴더는 B1 FastAPI 서버에 붙여 사용할 DB 모델, Alembic 마이그레이션, Pydantic 스키마, service 함수를 담당한다.

현재 결정된 흐름:

```text
Frontend -> B1 FastAPI API -> back2 service 함수 -> PostgreSQL
```

따라서 이 폴더에서는 FastAPI 라우터를 제공하지 않는다. 프론트와 통신하는 API 라우터, 응답 포맷, JWT 발급/검증은 B1에서 담당하고, 이 폴더는 DB 작업 함수를 제공한다.

## 설치

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp .env.example .env
python3 -m alembic upgrade head
```

`.env`의 `DATABASE_URL`은 로컬 PostgreSQL 정보에 맞게 수정해야 한다.

## 주요 폴더

| 경로 | 역할 |
| --- | --- |
| `app/core` | DB 설정, 세션, service 예외 |
| `app/models` | SQLAlchemy ORM 모델 |
| `app/schemas` | service 입출력용 Pydantic 스키마 |
| `app/services` | B1에서 직접 호출할 DB/service 함수 |
| `alembic` | DB 마이그레이션 |

## B1 연결 방식

B1 라우터에서는 HTTP로 back2를 호출하지 않고 service 함수를 직접 import해서 사용한다.

```python
from app.core.database import get_db
from app.core.exceptions import ServiceError
from app.schemas.user import CreateUser
from app.services.user_service import create_user


def register(payload, db):
    try:
        user = create_user(
            db,
            CreateUser(
                email=payload.email,
                password_hash=payload.password_hash,
                nickname=payload.nickname,
            ),
        )
    except ServiceError as exc:
        return {"state": "failure", "message": exc.message}

    return {"state": "success", "message": "요청 처리 성공", "data": {"user_id": user.id}}
```

## Service 예외

service 함수에서 업무 조건 실패가 발생하면 `ServiceError`를 발생시킨다.

```python
from app.core.exceptions import ServiceError
```

B1은 이 예외를 잡아서 팀 응답 규칙에 맞게 `failure` 응답으로 변환하면 된다.

## 주요 service

| service | 주요 함수 |
| --- | --- |
| `user_service.py` | `create_user`, `update_user`, `get_user_by_email`, `get_password_hash_by_email`, `get_user_id_by_email`, `get_nickname_by_email` |
| `auth_service.py` | `create_refresh_token`, `verify_refresh_token`, `revoke_refresh_token` |
| `admin_service.py` | 영화/캐릭터 CRUD, 관리자 통계 |
| `interaction_service.py` | 영화 조회/검색 후 조회/좋아요 기록 |
| `preference_service.py` | 사용자 취향 점수 조회/누적 |
| `ranking_service.py` | 인기 영화 랭킹 조회 |
| `user_activity_service.py` | 마이페이지 좋아요/조회 기록 조회 |

## 현재 DB 주요 테이블

| 테이블 | 목적 |
| --- | --- |
| `users` | 사용자 기본 정보 |
| `refresh_tokens` | Refresh Token hash 저장/검증/폐기 |
| `movies` | 영화 정보 |
| `characters` | 캐릭터 정보/프롬프트 |
| `user_movie_interactions` | 사용자 영화 행동 로그 |
| `user_preference_scores` | 사용자 취향 점수 |
| `movie_stats` | 영화 랭킹 누적 통계 |
| `chat_rooms` | 채팅방 정보 |
| `chat_messages` | 채팅 메시지 |
| `admin_audit_logs` | 관리자 작업 이력용 테이블, 현재 로직 미연결 |

## 완료된 범위

- PostgreSQL 스키마/Alembic 마이그레이션
- 사용자 생성/조회 service
- Refresh Token 저장/검증/폐기 service
- 영화/캐릭터 CRUD service
- 영화 조회/검색 후 조회/좋아요 기록 service
- 영화 인기 랭킹 service
- 영화 기반 취향 점수 누적 service
- 마이페이지용 취향/좋아요/조회 기록 조회 service

## 남은 범위

- B1 라우터에서 service 직접 호출로 연결
- 캐릭터 기반 취향 학습 로직
- 관리자 작업 이력 저장 로직
- 배포/CI/CD
