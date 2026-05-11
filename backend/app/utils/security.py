"""
密码安全工具
使用 bcrypt 进行密码哈希和验证
"""
import bcrypt
import secrets


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def generate_session_token() -> str:
    """生成安全的会话令牌"""
    return secrets.token_urlsafe(32)
