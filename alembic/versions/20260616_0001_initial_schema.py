"""initial schema

Revision ID: 20260616_0001
Revises:
Create Date: 2026-06-16
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260616_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 초기 DB 스키마의 모든 테이블과 제약조건을 생성한다.
    # 초기 마이그레이션은 기획 확정 스키마를 새 DB에 한 번에 구성한다.
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=False),
        sa.Column("preferred_genres", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_actors", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("preferred_keywords", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "movies",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tmdb_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column("genres", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("director", sa.String(length=200), nullable=True),
        sa.Column("cast", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("vote_average", sa.Float(), nullable=True),
        sa.Column("vote_count", sa.Integer(), nullable=True),
        sa.Column("audience_count", sa.BigInteger(), nullable=True),
        sa.Column("poster_path", sa.String(length=300), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_movies_title", "movies", ["title"])
    op.create_index("ix_movies_tmdb_id", "movies", ["tmdb_id"], unique=True)

    op.create_table(
        "characters",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("movie_id", sa.BigInteger(), sa.ForeignKey("movies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("movie_title", sa.String(length=200), nullable=False),
        sa.Column("actor", sa.String(length=100), nullable=True),
        sa.Column("lang", sa.String(length=10), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("profile_image", sa.String(length=300), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_characters_name", "characters", ["name"])

    op.create_table(
        "chat_rooms",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("room_type", sa.String(length=20), nullable=False),
        sa.Column("characters", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("room_type IN ('general', 'character', 'group')", name="ck_chat_rooms_room_type"),
    )
    op.create_index("ix_chat_rooms_user_id", "chat_rooms", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.BigInteger(), sa.ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("character_name", sa.String(length=100), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_messages_role"),
    )
    op.create_index("ix_chat_messages_room_id", "chat_messages", ["room_id"])

    op.create_table(
        "user_movie_interactions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("movie_id", sa.BigInteger(), sa.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=20), server_default="unknown", nullable=False),
        sa.Column("score_delta", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("action_type IN ('view', 'search_click', 'like')", name="ck_user_movie_interactions_action_type"),
        sa.CheckConstraint(
            "source IN ('direct', 'search', 'recommend', 'ranking', 'admin', 'unknown')",
            name="ck_user_movie_interactions_source",
        ),
    )
    op.create_index("ix_user_movie_interactions_user_id", "user_movie_interactions", ["user_id"])
    op.create_index("ix_user_movie_interactions_movie_id", "user_movie_interactions", ["movie_id"])
    op.create_index("ix_user_movie_interactions_created_at", "user_movie_interactions", ["created_at"])

    op.create_table(
        "user_preference_scores",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("preference_type", sa.String(length=20), nullable=False),
        sa.Column("preference_value", sa.String(length=200), nullable=False),
        sa.Column("score", sa.Float(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "preference_type IN ('genre', 'actor', 'director', 'keyword', 'language')",
            name="ck_user_preference_scores_preference_type",
        ),
        sa.UniqueConstraint("user_id", "preference_type", "preference_value", name="uq_user_preference_scores_value"),
    )
    op.create_index("ix_user_preference_scores_user_id", "user_preference_scores", ["user_id"])

    op.create_table(
        "movie_stats",
        sa.Column("movie_id", sa.BigInteger(), sa.ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("view_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("search_click_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("like_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ranking_score", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_movie_stats_ranking_score", "movie_stats", ["ranking_score"])

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("admin_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_table", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("before_data", sa.Text(), nullable=True),
        sa.Column("after_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # 초기 스키마에서 생성한 테이블을 역순으로 삭제한다.
    op.drop_table("admin_audit_logs")
    op.drop_index("ix_movie_stats_ranking_score", table_name="movie_stats")
    op.drop_table("movie_stats")
    op.drop_index("ix_user_preference_scores_user_id", table_name="user_preference_scores")
    op.drop_table("user_preference_scores")
    op.drop_index("ix_user_movie_interactions_created_at", table_name="user_movie_interactions")
    op.drop_index("ix_user_movie_interactions_movie_id", table_name="user_movie_interactions")
    op.drop_index("ix_user_movie_interactions_user_id", table_name="user_movie_interactions")
    op.drop_table("user_movie_interactions")
    op.drop_index("ix_chat_messages_room_id", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_rooms_user_id", table_name="chat_rooms")
    op.drop_table("chat_rooms")
    op.drop_index("ix_characters_name", table_name="characters")
    op.drop_table("characters")
    op.drop_index("ix_movies_tmdb_id", table_name="movies")
    op.drop_index("ix_movies_title", table_name="movies")
    op.drop_table("movies")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
