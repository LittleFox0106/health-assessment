"""
用户与会话管理 API
- POST /api/v1/users/init  — 初始化用户
- POST /api/v1/sessions    — 创建测评会话
- GET  /api/v1/sessions/:id/progress — 获取进度
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, AssessmentSession, AssessmentData
from app.schemas.schemas import ApiResponse, UserInfo, SessionInfo, ProgressData

router = APIRouter(prefix="/api/v1", tags=["users & sessions"])


@router.post("/users/init", response_model=ApiResponse)
def init_user(db: Session = Depends(get_db)):
    """初始化用户，生成 session_token"""
    session_token = secrets.token_urlsafe(32)
    user = User(session_token=session_token)
    db.add(user)
    db.commit()
    db.refresh(user)

    return ApiResponse(
        code=200,
        message="用户初始化成功",
        data=UserInfo(
            user_id=user.id,
            session_token=user.session_token,
        ).model_dump(),
    )


@router.post("/sessions", response_model=ApiResponse)
def create_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新的测评会话"""
    session = AssessmentSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)

    return ApiResponse(
        code=200,
        message="会话创建成功",
        data=SessionInfo(
            session_id=session.id,
            current_step=session.current_step,
            status=session.status,
        ).model_dump(),
    )


@router.get("/sessions/{session_id}/progress", response_model=ApiResponse)
def get_progress(
    session_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取会话进度，返回已填写的数据"""
    session = db.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.user_id == user.id,
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或不属于当前用户",
        )

    data = db.query(AssessmentData).filter(
        AssessmentData.session_id == session_id
    ).first()

    progress = ProgressData(
        session_id=session.id,
        current_step=session.current_step,
        status=session.status,
    )

    if data:
        progress.gender = data.gender
        progress.goal = data.goal
        progress.age = data.age
        progress.height_cm = float(data.height_cm) if data.height_cm else None
        progress.weight_kg = float(data.weight_kg) if data.weight_kg else None
        progress.target_weight_kg = float(data.target_weight_kg) if data.target_weight_kg else None
        progress.exercise_frequency = data.exercise_frequency

    return ApiResponse(
        code=200,
        message="获取进度成功",
        data=progress.model_dump(),
    )
