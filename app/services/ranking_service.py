from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.interaction import MovieStats
from app.models.movie import Movie


def list_top_movies(db: Session, limit: int = 10) -> list[dict]:
    # 누적 통계 테이블을 기준으로 상위 인기 영화를 조회한다.
    # 동점일 때 좋아요와 조회 수를 보조 정렬로 써서 결과 순서를 안정적으로 만든다.
    stmt = (
        select(
            MovieStats.movie_id,
            Movie.title,
            Movie.poster_path,
            MovieStats.view_count,
            MovieStats.search_click_count,
            MovieStats.like_count,
            MovieStats.ranking_score,
        )
        .join(Movie, Movie.id == MovieStats.movie_id)
        .order_by(desc(MovieStats.ranking_score), desc(MovieStats.like_count), desc(MovieStats.view_count))
        .limit(limit)
    )
    return [dict(row._mapping) for row in db.execute(stmt)]
