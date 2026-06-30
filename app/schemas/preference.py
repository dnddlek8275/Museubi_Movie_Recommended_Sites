from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PreferenceScoreRead(BaseModel):
    # 서비스에서 ORM 객체를 그대로 반환해도 공통 응답 포맷으로 감쌀 수 있게 둔다.
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    preference_type: str
    preference_value: str
    score: float
    created_at: datetime
    updated_at: datetime
