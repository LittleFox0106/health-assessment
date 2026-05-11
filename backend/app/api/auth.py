"""
用户认证 API
- POST /api/v1/auth/register  — 邮箱注册
- POST /api/v1/auth/login     — 邮箱登录
- GET  /api/v1/auth/profile   — 获取当前用户信息
- POST /api/v1/auth/link      — 将匿名账号关联到邮箱账号
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import User, Subscription
from app.schemas.schemas import ApiResponse
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserProfile
from app.utils.security import hash_password, verify_password, generate_session_token

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/register", response_model=ApiResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """邮箱注册，创建新用户"""
    # 检查邮箱是否已存在
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )

    # 创建新用户
    user = User(
        session_token=generate_session_token(),
        email=body.email,
        password_hash=hash_password(body.password),
        is_anonymous=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return ApiResponse(
        code=200,
        message="注册成功",
        data=AuthResponse(
            user_id=user.id,
            email=user.email,
            session_token=user.session_token,
            is_anonymous=user.is_anonymous,
        ).model_dump(),
    )


@router.post("/login", response_model=ApiResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """邮箱登录"""
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
        )

    # 生成新的 session_token
    user.session_token = generate_session_token()
    db.commit()

    return ApiResponse(
        code=200,
        message="登录成功",
        data=AuthResponse(
            user_id=user.id,
            email=user.email,
            session_token=user.session_token,
            is_anonymous=user.is_anonymous,
        ).model_dump(),
    )


@router.get("/profile", response_model=ApiResponse)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    # 检查是否有有效订阅
    has_sub = False
    if not user.is_anonymous:
        sub = db.query(Subscription).filter(
            Subscription.user_id == user.id,
            Subscription.status == "active"
        ).first()
        if sub:
            from datetime import datetime, timezone
            expires = sub.expires_at
            now = datetime.now(timezone.utc)
            if expires:
                if expires.tzinfo is None:
                    now = datetime.now()
                has_sub = expires > now

    return ApiResponse(
        code=200,
        message="获取成功",
        data=UserProfile(
            user_id=user.id,
            email=user.email,
            is_anonymous=user.is_anonymous,
            has_subscription=has_sub,
        ).model_dump(),
    )


@router.post("/link", response_model=ApiResponse)
def link_anonymous_account(
    body: RegisterRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """将当前匿名账号关联到邮箱（升级账号）"""
    if not user.is_anonymous:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前账号已关联邮箱",
        )

    # 检查邮箱是否已被使用
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )

    # 更新用户信息
    user.email = body.email
    user.password_hash = hash_password(body.password)
    user.is_anonymous = False
    db.commit()

    return ApiResponse(
        code=200,
        message="账号升级成功",
        data=AuthResponse(
            user_id=user.id,
            email=user.email,
            session_token=user.session_token,
            is_anonymous=user.is_anonymous,
        ).model_dump(),
    )
