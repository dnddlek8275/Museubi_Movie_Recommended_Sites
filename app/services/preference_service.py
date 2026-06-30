from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models.interaction import UserPreferenceScore
from app.models.movie import Movie
from app.models.user import User

PREFERENCE_SCORE = {
    # 취향 점수는 개인 선호 강도 기준이라 랭킹 점수보다 세밀하게 둔다.
    "view": 0.5,
    "search_click": 0.8,
    "like": 2.0,
}


def list_user_preference_scores(
    db: Session,
    user_id: int,
    *,
    preference_type: str | None = None,
    limit: int = 20,
) -> list[UserPreferenceScore]:
    # 사용자별 취향 점수를 조건에 맞게 조회한다.
    if db.get(User, user_id) is None:
        raise ServiceError("사용자를 찾을 수 없습니다.", status_code=404)

    stmt = (
        select(UserPreferenceScore)
        .where(UserPreferenceScore.user_id == user_id)
    )
    if preference_type is not None:
        stmt = stmt.where(UserPreferenceScore.preference_type == preference_type)
    stmt = stmt.order_by(UserPreferenceScore.score.desc(), UserPreferenceScore.preference_value.asc()).limit(limit)
    return list(db.scalars(stmt).all())


def update_user_preference_scores(
    db: Session,
    *,
    user_id: int,
    movie: Movie,
    action_type: str,
) -> None:
    # 영화 행동을 사용자 취향 축별 점수로 변환해 누적한다.
    score_delta = PREFERENCE_SCORE[action_type]
    preference_items = collect_movie_preference_items(movie)

    for preference_type, preference_value in preference_items:
        # 같은 취향값은 row를 늘리지 않고 점수만 누적해 추천 조회를 단순하게 만든다.
        stmt = insert(UserPreferenceScore).values(
            user_id=user_id,
            preference_type=preference_type,
            preference_value=preference_value,
            score=score_delta,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_user_preference_scores_value",
            set_={
                "score": UserPreferenceScore.score + score_delta,
            },
        )
        db.execute(stmt)


def collect_movie_preference_items(movie: Movie) -> list[tuple[str, str]]:
    # 영화 메타데이터에서 취향 점수로 저장할 항목 목록을 만든다.
    # 영화 메타데이터를 취향 축으로 바꿔 저장하면 추천 로직이 테이블 하나만 조회하면 된다.
    items: list[tuple[str, str]] = []
    items.extend(("genre", value) for value in normalize_values(movie.genres))
    items.extend(("actor", value) for value in normalize_values(movie.cast))
    items.extend(("keyword", value) for value in normalize_values(movie.keywords))
    if movie.director:
        items.append(("director", movie.director.strip()))
    if movie.language:
        items.append(("language", movie.language.strip()))
    return [(item_type, item_value) for item_type, item_value in items if item_value]


def normalize_values(values: list[str] | None) -> list[str]:
    # 배열형 문자열 값에서 빈 값을 제거하고 앞뒤 공백을 정리한다.
    if not values:
        return []
    return [value.strip() for value in values if value and value.strip()]
