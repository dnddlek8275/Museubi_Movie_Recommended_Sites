from pydantic import BaseModel


class AdminStatsRead(BaseModel):
    # 관리자 통계는 여러 테이블의 집계 결과라 ORM 모델과 직접 1:1로 묶지 않는다.
    user_count: int
    movie_count: int
    character_count: int
    interaction_count: int
    top_movies: list[dict]
