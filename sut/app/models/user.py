from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SqlEnum
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)  # 用户名
    email = Column(String(100), unique=True, nullable=False, index=True)    # 邮箱
    password_hash = Column(String(255), nullable=False)                      # 密码哈希
    role = Column(SqlEnum(UserRole), default=UserRole.MEMBER, nullable=False)  # 角色
    avatar = Column(String(255), default="")                                  # 头像URL
    created_at = Column(DateTime, default=datetime.now)                       # 创建时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)  # 更新时间
