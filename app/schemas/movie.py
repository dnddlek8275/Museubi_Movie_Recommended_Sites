from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateMovie(BaseModel):
    # TMDB에 없는 자체 입력 영화도 저장할 수 있어 tmdb_id는 선택값으로 둔다.
    tmdb_id: int | None = None
    title: str = Field(min_length=1, max_length=300)
    overview: str | None = None
    genres: list[str] | None = None
    director: str | None = Field(default=None, max_length=200)
    cast: list[str] | None = None
    keywords: list[str] | None = None
    year: int | None = None
    language: str | None = Field(default=None, max_length=10)
    vote_average: float | None = None
    vote_count: int | None = None
    audience_count: int | None = None
    poster_path: str | None = Field(default=None, max_length=300)
    last_synced_at: datetime | None = None


class UpdateMovie(BaseModel):
    # 수정 API는 부분 수정 용도라 모든 필드를 선택값으로 둔다.
    tmdb_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    overview: str | None = None
    genres: list[str] | None = None
    director: str | None = Field(default=None, max_length=200)
    cast: list[str] | None = None
    keywords: list[str] | None = None
    year: int | None = None
    language: str | None = Field(default=None, max_length=10)
    vote_average: float | None = None
    vote_count: int | None = None
    audience_count: int | None = None
    poster_path: str | None = Field(default=None, max_length=300)
    last_synced_at: datetime | None = None


class ReadMovie(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tmdb_id: int | None
    title: str
    overview: str | None
    genres: list[str] | None
    director: str | None
    cast: list[str] | None
    keywords: list[str] | None
    year: int | None
    language: str | None
    vote_average: float | None
    vote_count: int | None
    audience_count: int | None
    poster_path: str | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
