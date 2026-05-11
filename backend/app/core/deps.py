"""
FastAPI 依赖注入
从请求头中提取 session_token，获取当前用户
"""
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import User


def get_current_user(
    x_session_token: str = Header(..., alias="X-Session-Token"),
    db: Session = Depends(get_db),
) -> User:
    """根据 X-Session-Token 请求头获取当前用户"""
    user = db.query(User).filter(User.session_token == x_session_token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的会话令牌，请重新初始化",
        )
    return user


def get_optional_user(
    x_session_token: str | None = Header(None, alias="X-Session-Token"),
    db: Session = Depends(get_db),
) -> User | None:
    """可选的用户认证（不强制要求 token）"""
    if not x_session_token:
        return None
    return db.query(User).filter(User.session_token == x_session_token).first()
