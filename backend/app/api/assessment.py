"""
测评数据分步保存 API
- PATCH /api/v1/sessions/:id/step/1 — 保存性别 + 目标
- PATCH /api/v1/sessions/:id/step/2 — 保存年龄 + 身高 + 体重
- PATCH /api/v1/sessions/:id/step/3 — 保存目标体重 + 运动频率
- POST  /api/v1/sessions/:id/submit — 提交所有数据，触发计算
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, AssessmentSession, AssessmentData
from app.schemas.schemas import (
    ApiResponse, Step1Input, Step2Input, Step3Input,
    SessionInfo, AssessmentResult,
)
from app.services.assessment import run_full_assessment

router = APIRouter(prefix="/api/v1/sessions", tags=["assessment data"])


def _get_session_or_404(session_id: str, user_id: str, db: Session) -> AssessmentSession:
    """获取会话，不存在则 404"""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_id == user_id,
    ).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或不属于当前用户",
        )
    return session


def _get_or_create_data(session_id: str, db: Session) -> AssessmentData:
    """获取或创建测评数据记录（UPSERT）"""
    data = db.query(AssessmentData).filter(
        AssessmentData.session_id == session_id
    ).first()
    if not data:
        data = AssessmentData(session_id=session_id)
        db.add(data)
        db.flush()
    return data


@router.patch("/{session_id}/step/1", response_model=ApiResponse)
def save_step1(
    session_id: str,
    body: Step1Input,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存第 1 步：性别 + 目标"""
    session = _get_session_or_404(session_id, user.id, db)
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="该会话已完成或已放弃")

    data = _get_or_create_data(session_id, db)
    data.gender = body.gender.value
    data.goal = body.goal.value
    data.step = max(data.step, 1)
    data.updated_at = datetime.now(timezone.utc)

    session.current_step = 2
    db.commit()
    db.refresh(session)

    return ApiResponse(
        code=200,
        message="第 1 步保存成功",
        data=SessionInfo(
            session_id=session.id,
            current_step=session.current_step,
            status=session.status,
        ).model_dump(),
    )


@router.patch("/{session_id}/step/2", response_model=ApiResponse)
def save_step2(
    session_id: str,
    body: Step2Input,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存第 2 步：年龄 + 身高 + 体重"""
    session = _get_session_or_404(session_id, user.id, db)
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="该会话已完成或已放弃")

    data = _get_or_create_data(session_id, db)
    data.age = body.age
    data.height_cm = body.height_cm
    data.weight_kg = body.weight_kg
    data.step = max(data.step, 2)
    data.updated_at = datetime.now(timezone.utc)

    session.current_step = 3
    db.commit()
    db.refresh(session)

    return ApiResponse(
        code=200,
        message="第 2 步保存成功",
        data=SessionInfo(
            session_id=session.id,
            current_step=session.current_step,
            status=session.status,
        ).model_dump(),
    )


@router.patch("/{session_id}/step/3", response_model=ApiResponse)
def save_step3(
    session_id: str,
    body: Step3Input,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存第 3 步：目标体重 + 运动频率"""
    session = _get_session_or_404(session_id, user.id, db)
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="该会话已完成或已放弃")

    data = _get_or_create_data(session_id, db)
    data.target_weight_kg = body.target_weight_kg
    data.exercise_frequency = body.exercise_frequency.value
    data.step = max(data.step, 3)
    data.updated_at = datetime.now(timezone.utc)

    session.current_step = 4
    db.commit()
    db.refresh(session)

    return ApiResponse(
        code=200,
        message="第 3 步保存成功",
        data=SessionInfo(
            session_id=session.id,
            current_step=session.current_step,
            status=session.status,
        ).model_dump(),
    )


@router.post("/{session_id}/submit", response_model=ApiResponse)
def submit_assessment(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交所有数据，触发服务端健康评估计算"""
    session = _get_session_or_404(session_id, user.id, db)
    if session.status != "in_progress":
        raise HTTPException(status_code=400, detail="该会话已完成或已放弃")

    data = db.query(AssessmentData).filter(
        AssessmentData.session_id == session_id
    ).first()

    if not data or not all([data.gender, data.goal, data.age, data.height_cm,
                            data.weight_kg, data.target_weight_kg, data.exercise_frequency]):
        raise HTTPException(
            status_code=400,
            detail="数据不完整，请确保所有步骤都已填写",
        )

    # 执行健康评估算法
    result = run_full_assessment(
        gender=data.gender,
        goal=data.goal,
        age=data.age,
        height_cm=float(data.height_cm),
        weight_kg=float(data.weight_kg),
        target_weight_kg=float(data.target_weight_kg),
        exercise_frequency=data.exercise_frequency,
    )

    # 保存计算结果
    data.bmi_value = result["bmi_value"]
    data.bmi_category = result["bmi_category"]
    data.bmr = result["bmr"]
    data.tdee = result["tdee"]
    data.daily_calorie_intake = result["daily_calorie_intake"]
    data.target_prediction_days = result["target_prediction_days"]
    data.protein_g = result["protein_g"]
    data.carbs_g = result["carbs_g"]
    data.fat_g = result["fat_g"]
    data.weekly_weight_change_kg = result["weekly_weight_change_kg"]
    data.updated_at = datetime.now(timezone.utc)

    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    db.commit()

    return ApiResponse(
        code=200,
        message="测评提交成功，评估计算完成",
        data={"session_id": session.id, "status": session.status},
    )
