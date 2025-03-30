from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["用户"])


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    avatar: str

    class Config:
        from_attributes = True


class UpdateUserRequest(BaseModel):
    email: str = Field(None, max_length=100)
    avatar: str = Field(None, max_length=255)


@router.get("/me", summary="获取当前用户信息", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", summary="更新个人信息", response_model=UserResponse)
def update_me(
    req: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.email is not None:
        # 检查邮箱唯一性
        existing = db.query(User).filter(User.email == req.email, User.id != current_user.id).first()
        if existing:
            return {"code": 400, "msg": "邮箱已被其他用户使用", "data": None}
        current_user.email = req.email
    if req.avatar is not None:
        current_user.avatar = req.avatar

    db.commit()
    db.refresh(current_user)
    return current_user
