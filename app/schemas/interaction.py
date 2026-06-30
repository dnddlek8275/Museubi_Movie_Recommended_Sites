from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.movie import ReadMovie


class MovieInteractionCreate(BaseModel):
    # JWT 연동 전까지는 user_id를 요청 body로 직접 넘겨 테스트한다.
    user_id: int
    source: str = Field(default="direct", pattern="^(direct|search|recommend|ranking|admin|unknown)$")


class MovieInteractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    movie_id: int
    action_type: str
    source: str
    score_delta: int
    created_at: datetime


class UserMovieRecordRead(BaseModel):
    interaction_id: int
    action_type: str
    source: str
    created_at: datetime
    movie: ReadMovie
