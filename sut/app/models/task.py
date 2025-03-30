from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SqlEnum
import enum

from app.database import Base


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class TaskPriority(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


# 状态流转规则：哪些状态可以转到哪些状态
STATUS_TRANSITIONS = {
    TaskStatus.TODO: [TaskStatus.IN_PROGRESS],
    TaskStatus.IN_PROGRESS: [TaskStatus.DONE, TaskStatus.TODO],
    TaskStatus.DONE: [TaskStatus.ARCHIVED, TaskStatus.IN_PROGRESS],
    TaskStatus.ARCHIVED: [TaskStatus.DONE],
}


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)                       # 任务标题
    description = Column(Text, default="")                             # 任务描述
    status = Column(SqlEnum(TaskStatus), default=TaskStatus.TODO)      # 状态
    priority = Column(SqlEnum(TaskPriority), default=TaskPriority.P2)  # 优先级
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 指派人
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 创建者
    due_date = Column(DateTime, nullable=True)                          # 截止日期
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)       # 评论内容
    created_at = Column(DateTime, default=datetime.now)
