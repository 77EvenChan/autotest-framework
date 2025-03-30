import re
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.middleware.auth import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user
)
from app.utils.exceptions import BizError, AuthError, RateLimitError
from app.utils.redis_client import redis_client
from app.config import MAX_LOGIN_ATTEMPTS, LOGIN_LOCK_SECONDS

router = APIRouter(prefix="/api/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", summary="用户注册")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # 参数校验
    if not re.match(r"^[a-zA-Z0-9_]+$", req.username):
        raise BizError(msg="用户名只能包含字母、数字和下划线")
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", req.email):
        raise BizError(msg="邮箱格式不正确")

    # 唯一性检查
    if db.query(User).filter(User.username == req.username).first():
        raise BizError(msg="用户名已存在")
    if db.query(User).filter(User.email == req.email).first():
        raise BizError(msg="邮箱已被注册")

    # 密码强度
    if len(req.password) < 6:
        raise BizError(msg="密码长度不能少于6位")

    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"code": 200, "msg": "注册成功", "data": {"user_id": user.id, "username": user.username}}


@router.post("/login", summary="用户登录", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # 登录失败次数限制
    lock_key = f"login_lock:{req.username}"
    attempt_key = f"login_attempts:{req.username}"

    if redis_client.get(lock_key):
        raise RateLimitError(msg="登录失败次数过多，账号已锁定30分钟")

    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        # 记录失败次数
        attempts = redis_client.incr(attempt_key)
        if attempts == 1:
            redis_client.expire(attempt_key, LOGIN_LOCK_SECONDS)
        if attempts >= MAX_LOGIN_ATTEMPTS:
            redis_client.setex(lock_key, LOGIN_LOCK_SECONDS, "1")
            raise RateLimitError(msg="登录失败次数过多，账号已锁定30分钟")
        raise BizError(msg="用户名或密码错误")

    # 登录成功，清除失败记录
    redis_client.delete(attempt_key)

    return {
        "access_token": create_access_token(user.id, user.username),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer"
    }


@router.post("/refresh", summary="刷新Token", response_model=TokenResponse)
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise AuthError(msg="Token类型错误，请使用refresh_token")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthError(msg="用户不存在")

    return {
        "access_token": create_access_token(user.id, user.username),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer"
    }
