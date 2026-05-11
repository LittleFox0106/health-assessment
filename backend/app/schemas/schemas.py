"""
Pydantic 请求/响应 Schema
定义所有 API 的输入输出数据结构
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import enum


# ==================== Enums ====================
class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class GoalEnum(str, enum.Enum):
    lose_weight = "lose_weight"
    gain_muscle = "gain_muscle"
    maintain = "maintain"
    improve_endurance = "improve_endurance"


class ExerciseFrequencyEnum(str, enum.Enum):
    never = "never"
    one_two = "1-2_times"
    three_five = "3-5_times"
    daily = "daily"


class SessionStatusEnum(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class SubscriptionStatusEnum(str, enum.Enum):
    active = "active"
    expired = "expired"
    cancelled = "cancelled"


# ==================== Step 1 Schemas ====================
class Step1Input(BaseModel):
    gender: GenderEnum
    goal: GoalEnum


# ==================== Step 2 Schemas ====================
class Step2Input(BaseModel):
    age: int = Field(ge=1, le=120)
    height_cm: float = Field(ge=50, le=300)
    weight_kg: float = Field(ge=20, le=500)


# ==================== Step 3 Schemas ====================
class Step3Input(BaseModel):
    target_weight_kg: float = Field(ge=20, le=500)
    exercise_frequency: ExerciseFrequencyEnum


# ==================== Response Schemas ====================
class UserInfo(BaseModel):
    user_id: str
    session_token: str


class SessionInfo(BaseModel):
    session_id: str
    current_step: int
    status: str


class ProgressData(BaseModel):
    session_id: str
    current_step: int
    status: str
    gender: Optional[str] = None
    goal: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    exercise_frequency: Optional[str] = None


class AssessmentResult(BaseModel):
    session_id: str
    bmi_value: Optional[float] = None
    bmi_category: Optional[str] = None
    daily_calorie_intake: Optional[int] = None
    bmr: Optional[float] = None
    tdee: Optional[float] = None
    target_prediction_days: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    weekly_weight_change_kg: Optional[float] = None
    is_premium: bool = False


class PayRequest(BaseModel):
    user_id: Optional[str] = None


class PayResponse(BaseModel):
    user_id: str
    subscription_status: str
    plan_type: str
    started_at: datetime
    expires_at: Optional[datetime] = None


class SubscriptionStatus(BaseModel):
    user_id: str
    status: str
    plan_type: Optional[str] = None
    is_active: bool


# ==================== Unified Response ====================
class ApiResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict | list] = None


class ErrorResponse(BaseModel):
    code: int = 400
    message: str
    details: Optional[list[dict]] = None
