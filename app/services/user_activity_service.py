from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceError
from app.models.interaction import UserMovieInteraction
from app.models.movie import Movie
from app.models.user import User
from app.schemas.interaction import UserMovieRecordRead
from app.schemas.movie import ReadMovie


def list_user_liked_movies(db: Session, user_id: int, limit: int = 20) -> list[dict]:
    # 마이페이지용 사용자 좋아요 영화 목록을 영화 단위로 조회한다.
    ensure_user_exists(db, user_id)

    latest_like = (
        select(
            UserMovieInteraction.movie_id,
            func.max(UserMovieInteraction.created_at).label("latest_created_at"),
        )
        .where(
            UserMovieInteraction.user_id == user_id,
            UserMovieInteraction.action_type == "like",
        )
        .group_by(UserMovieInteraction.movie_id)
        .subquery()
    )

    # 좋아요는 같은 영화를 여러 번 눌러도 마이페이지에서는 영화 단위로 보여준다.
    stmt = (
        select(UserMovieInteraction, Movie)
        .join(Movie, Movie.id == UserMovieInteraction.movie_id)
        .join(
            latest_like,
            (latest_like.c.movie_id == UserMovieInteraction.movie_id)
            & (latest_like.c.latest_created_at == UserMovieInteraction.created_at),
        )
        .where(
            UserMovieInteraction.user_id == user_id,
            UserMovieInteraction.action_type == "like",
        )
        .order_by(UserMovieInteraction.created_at.desc(), UserMovieInteraction.id.desc())
        .limit(limit)
    )
    return [build_user_movie_record(interaction, movie) for interaction, movie in db.execute(stmt).all()]


def list_user_view_history(db: Session, user_id: int, limit: int = 20) -> list[dict]:
    # 마이페이지용 사용자 최근 영화 조회 기록을 조회한다.
    ensure_user_exists(db, user_id)

    stmt = (
        select(UserMovieInteraction, Movie)
        .join(Movie, Movie.id == UserMovieInteraction.movie_id)
        .where(
            UserMovieInteraction.user_id == user_id,
            UserMovieInteraction.action_type.in_(["view", "search_click"]),
        )
        .order_by(UserMovieInteraction.created_at.desc(), UserMovieInteraction.id.desc())
        .limit(limit)
    )
    return [build_user_movie_record(interaction, movie) for interaction, movie in db.execute(stmt).all()]


def ensure_user_exists(db: Session, user_id: int) -> None:
    # 사용자 ID가 실제 존재하는지 확인한다.
    if db.get(User, user_id) is None:
        raise ServiceError("사용자를 찾을 수 없습니다.", status_code=404)


def build_user_movie_record(interaction: UserMovieInteraction, movie: Movie) -> dict:
    # 행동 로그와 영화 정보를 마이페이지 응답 형태로 합친다.
    return UserMovieRecordRead(
        interaction_id=interaction.id,
        action_type=interaction.action_type,
        source=interaction.source,
        created_at=interaction.created_at,
        movie=ReadMovie.model_validate(movie),
    ).model_dump()
