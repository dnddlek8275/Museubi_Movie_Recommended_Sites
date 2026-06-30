from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class Character(TimestampMixin, Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # 영화가 삭제되어도 캐릭터 대화 설정은 남길 수 있게 연결만 해제한다.
    movie_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("movies.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    movie_title: Mapped[str] = mapped_column(String(200), nullable=False)
    actor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lang: Mapped[str] = mapped_column(String(10), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    profile_image: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    movie = relationship("Movie")
