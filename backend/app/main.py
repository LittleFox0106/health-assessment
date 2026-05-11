"""
FastAPI 主应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import os

from app.core.database import init_db
from app.api.sessions import router as sessions_router
from app.api.assessment import router as assessment_router
from app.api.subscription import router as subscription_router
from app.api.auth import router as auth_router

app = FastAPI(
    title="健康测评系统 API",
    description="Health Assessment System - Full Stack Challenge",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(sessions_router)
app.include_router(assessment_router)
app.include_router(subscription_router)
app.include_router(auth_router)


# 静态文件托管（前端页面）
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


@app.on_event("startup")
def on_startup():
    """应用启动时初始化数据库"""
    init_db()
    print("✅ 数据库初始化完成")


# 前端页面路由（禁用缓存，开发阶段）
@app.get("/")
def serve_index():
    html_path = os.path.join(STATIC_DIR, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="text/html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


# 挂载静态资源目录
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
