from pydantic import BaseModel


class MovieRankingRead(BaseModel):
    # 랭킹 결과는 점수 계산 근거를 같이 보여줘 화면 표시와 검증에 쓰기 쉽게 둔다.
    movie_id: int
    title: str
    poster_path: str | None
    view_count: int
    search_click_count: int
    like_count: int
    ranking_score: int
