from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models.interaction import MovieStats, UserMovieInteraction
from app.models.movie import Movie
from app.models.user import User
from app.services.preference_service import update_user_preference_scores

ACTION_SCORE = {
    # 랭킹 점수는 대중적 인기 기준이라 취향 학습 점수와 분리한다.
    "view": 1,
    "search_click": 1,
    "like": 2,
}


def resolve_action_type(source: str) -> str:
    # 조회 출처를 실제 저장할 행동 타입으로 변환한다.
    # 상세 조회 API 하나로 일반 조회와 검색 후 조회를 구분하기 위한 변환이다.
    if source == "search":
        return "search_click"
    return "view"


def record_movie_interaction(
    db: Session,
    *,
    user_id: int,
    movie_id: int,
    action_type: str,
    source: str = "unknown",
) -> UserMovieInteraction:
    # 사용자 영화 행동을 저장하고 랭킹/취향 점수를 함께 갱신한다.
    if db.get(User, user_id) is None:
        raise ServiceError("사용자를 찾을 수 없습니다.", status_code=404)
    movie = db.get(Movie, movie_id)
    if movie is None:
        raise ServiceError("영화를 찾을 수 없습니다.", status_code=404)

    score_delta = ACTION_SCORE[action_type]
    interaction = UserMovieInteraction(
        user_id=user_id,
        movie_id=movie_id,
        action_type=action_type,
        source=source,
        score_delta=score_delta,
    )
    db.add(interaction)

    # movie_stats는 랭킹 조회를 빠르게 하기 위해 로그 전체를 매번 집계하지 않고 누적 갱신한다.
    count_column_by_action = {
        "view": "view_count",
        "search_click": "search_click_count",
        "like": "like_count",
    }
    count_column = count_column_by_action[action_type]
    stmt = insert(MovieStats).values(
        movie_id=movie_id,
        view_count=1 if action_type == "view" else 0,
        search_click_count=1 if action_type == "search_click" else 0,
        like_count=1 if action_type == "like" else 0,
        ranking_score=score_delta,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[MovieStats.movie_id],
        set_={
            count_column: getattr(MovieStats, count_column) + 1,
            "ranking_score": MovieStats.ranking_score + score_delta,
        },
    )
    db.execute(stmt)
    # 같은 사용자 행동에서 랭킹과 개인 취향을 함께 갱신해 데이터 누락을 줄인다.
    update_user_preference_scores(db, user_id=user_id, movie=movie, action_type=action_type)
    db.commit()
    db.refresh(interaction)
    return interaction
