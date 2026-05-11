"""
结果查询与订阅管理 API
- GET  /api/v1/sessions/:id/result        — 获取测评结果（差异化返回）
- POST /api/v1/pay                        — 模拟支付回调
- GET  /api/v1/subscription/status        — 查询订阅状态
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, AssessmentSession, AssessmentData, Subscription
from app.schemas.schemas import (
    ApiResponse, AssessmentResult, PayRequest, PayResponse, SubscriptionStatus,
)

router = APIRouter(prefix="/api/v1", tags=["results & subscription"])


def _is_subscription_active(subscription: Subscription) -> bool:
    """检查订阅是否有效（兼容 naive 和 aware datetime）"""
    if subscription.status != "active":
        return False
    if not subscription.expires_at:
        return False
    now = datetime.now(timezone.utc)
    expires = subscription.expires_at
    # 兼容 SQLite 的 naive datetime
    if expires.tzinfo is None:
        now = datetime.now()
    return expires > now


@router.get("/sessions/{session_id}/result", response_model=ApiResponse)
def get_result(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取测评结果，根据订阅状态差异化返回"""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_id == user.id,
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    data = db.query(AssessmentData).filter(
        AssessmentData.session_id == session_id
    ).first()

    if not data:
        raise HTTPException(status_code=404, detail="测评数据不存在")

    # 检查订阅状态
    is_premium = False
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active",
    ).first()
    if subscription:
        if _is_subscription_active(subscription):
            is_premium = True

    result = AssessmentResult(
        session_id=session.id,
        bmi_value=float(data.bmi_value) if data.bmi_value else None,
        bmi_category=data.bmi_category,
        daily_calorie_intake=data.daily_calorie_intake,
        bmr=float(data.bmr) if data.bmr else None,
        tdee=float(data.tdee) if data.tdee else None,
        is_premium=is_premium,
    )

    if is_premium:
        # 会员返回完整数据
        result.target_prediction_days = data.target_prediction_days
        result.protein_g = float(data.protein_g) if data.protein_g else None
        result.carbs_g = float(data.carbs_g) if data.carbs_g else None
        result.fat_g = float(data.fat_g) if data.fat_g else None
        result.weekly_weight_change_kg = float(data.weekly_weight_change_kg) if data.weekly_weight_change_kg else None
    else:
        # 非会员隐藏高级数据
        result.target_prediction_days = None
        result.protein_g = None
        result.carbs_g = None
        result.fat_g = None
        result.weekly_weight_change_kg = None

    return ApiResponse(
        code=200,
        message="获取结果成功",
        data=result.model_dump(),
    )


@router.post("/pay", response_model=ApiResponse)
def simulate_pay(
    body: PayRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """模拟支付回调，激活会员状态"""
    target_user = user
    if body.user_id:
        target_user = db.query(User).filter(User.id == body.user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")

    # 查找或创建订阅
    subscription = db.query(Subscription).filter(
        Subscription.user_id == target_user.id
    ).first()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30)

    if subscription:
        subscription.status = "active"
        subscription.plan_type = "premium"
        subscription.started_at = now
        subscription.expires_at = expires_at
    else:
        subscription = Subscription(
            user_id=target_user.id,
            status="active",
            plan_type="premium",
            started_at=now,
            expires_at=expires_at,
        )
        db.add(subscription)

    db.commit()
    db.refresh(subscription)

    return ApiResponse(
        code=200,
        message="支付成功，会员已激活",
        data=PayResponse(
            user_id=target_user.id,
            subscription_status=subscription.status,
            plan_type=subscription.plan_type or "premium",
            started_at=subscription.started_at,
            expires_at=subscription.expires_at,
        ).model_dump(),
    )


@router.get("/subscription/status", response_model=ApiResponse)
def get_subscription_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询当前用户订阅状态"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id
    ).first()

    if not subscription:
        return ApiResponse(
            code=200,
            message="查询成功",
            data=SubscriptionStatus(
                user_id=user.id,
                status="none",
                plan_type=None,
                is_active=False,
            ).model_dump(),
        )

    is_active = _is_subscription_active(subscription)

    return ApiResponse(
        code=200,
        message="查询成功",
        data=SubscriptionStatus(
            user_id=user.id,
            status=subscription.status,
            plan_type=subscription.plan_type,
            is_active=is_active,
        ).model_dump(),
    )
