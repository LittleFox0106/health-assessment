"""
SQLAlchemy 数据模型
包含 4 张核心表：users, assessment_sessions, assessment_data, subscriptions
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, SmallInteger, Numeric, DateTime, ForeignKey, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    session_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    # 新增：邮箱登录相关字段
    email: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    is_anonymous: Mapped[bool] = mapped_column(
        default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # 关系
    sessions: Mapped[list["AssessmentSession"]] = relationship(
        "AssessmentSession", back_populates="user", cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    current_step: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="in_progress"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    assessment_data: Mapped["AssessmentData | None"] = relationship(
        "AssessmentData", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )


class AssessmentData(Base):
    __tablename__ = "assessment_data"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assessment_sessions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    step: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1
    )

    # 第 1 步数据
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    goal: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 第 2 步数据
    age: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)

    # 第 3 步数据
    target_weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    exercise_frequency: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # 计算结果（提交后填充）
    bmi_value: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    bmi_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    daily_calorie_intake: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    target_prediction_days: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    bmr: Mapped[float | None] = mapped_column(Numeric(7, 1), nullable=True)
    tdee: Mapped[float | None] = mapped_column(Numeric(7, 1), nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    weekly_weight_change_kg: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # 关系
    session: Mapped["AssessmentSession"] = relationship("AssessmentSession", back_populates="assessment_data")

    # 表级约束
    __table_args__ = (
        CheckConstraint("age IS NULL OR (age >= 1 AND age <= 120)", name="ck_age_range"),
        CheckConstraint("height_cm IS NULL OR (height_cm >= 50 AND height_cm <= 300)", name="ck_height_range"),
        CheckConstraint("weight_kg IS NULL OR (weight_kg >= 20 AND weight_kg <= 500)", name="ck_weight_range"),
        CheckConstraint("target_weight_kg IS NULL OR (target_weight_kg >= 20 AND target_weight_kg <= 500)", name="ck_target_weight_range"),
        CheckConstraint("step >= 1 AND step <= 4", name="ck_step_range"),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=_generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="expired"
    )
    plan_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True, default="premium"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="subscription")
