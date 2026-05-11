"""
初始化测试账号脚本
创建两个测试账号：
1. test@example.com - 未支付用户
2. vip@example.com - 已支付用户（会员有效期30天）

密码均为：123456
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal, init_db
from app.models.models import User, Subscription
from app.utils.security import hash_password, generate_session_token


def create_test_users():
    """创建测试用户"""
    db = SessionLocal()
    
    try:
        # 检查是否已存在
        existing_test = db.query(User).filter(User.email == "test@example.com").first()
        existing_vip = db.query(User).filter(User.email == "vip@example.com").first()
        
        if existing_test and existing_vip:
            print("✅ 测试账号已存在")
            print(f"\n📧 未支付账号: test@example.com / 123456")
            print(f"📧 已支付账号: vip@example.com / 123456")
            return
        
        # 1. 创建未支付用户
        if not existing_test:
            test_user = User(
                session_token=generate_session_token(),
                email="test@example.com",
                password_hash=hash_password("123456"),
                is_anonymous=False,
            )
            db.add(test_user)
            db.flush()
            
            # 不创建订阅记录（或创建过期状态）
            expired_sub = Subscription(
                user_id=test_user.id,
                status="expired",
                plan_type="premium",
                started_at=datetime.now(timezone.utc) - timedelta(days=60),
                expires_at=datetime.now(timezone.utc) - timedelta(days=30),
            )
            db.add(expired_sub)
            print(f"✅ 创建未支付用户: test@example.com (ID: {test_user.id})")
        
        # 2. 创建已支付用户
        if not existing_vip:
            vip_user = User(
                session_token=generate_session_token(),
                email="vip@example.com",
                password_hash=hash_password("123456"),
                is_anonymous=False,
            )
            db.add(vip_user)
            db.flush()
            
            # 创建有效订阅
            active_sub = Subscription(
                user_id=vip_user.id,
                status="active",
                plan_type="premium",
                started_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            db.add(active_sub)
            print(f"✅ 创建已支付用户: vip@example.com (ID: {vip_user.id})")
        
        db.commit()
        
        print("\n" + "="*50)
        print("🎉 测试账号创建成功！")
        print("="*50)
        print("\n📧 账号 1 (未支付):")
        print("   邮箱: test@example.com")
        print("   密码: 123456")
        print("   状态: 无有效订阅")
        print("\n📧 账号 2 (已支付):")
        print("   邮箱: vip@example.com")
        print("   密码: 123456")
        print("   状态: 会员有效（30天）")
        print("\n💡 使用说明:")
        print("   1. 打开 http://localhost:8000")
        print("   2. 点击右上角'登录/注册'")
        print("   3. 使用上述账号登录测试")
        print("="*50)
        
    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🔧 初始化测试账号...\n")
    init_db()  # 确保表已创建
    create_test_users()
