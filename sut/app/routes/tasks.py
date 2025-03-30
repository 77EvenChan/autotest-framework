from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.project import ProjectMember
from app.models.task import Task, TaskComment, TaskStatus, TaskPriority, STATUS_TRANSITIONS
from app.routes.projects import check_project_member
from app.middleware.auth import get_current_user
from app.utils.exceptions import BizError, NotFoundError, ForbiddenError

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


class CreateTaskRequest(BaseModel):
    project_id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=2000)
    priority: str = Field("P2", pattern="^(P0|P1|P2|P3)$")
    assignee_id: Optional[int] = None
    due_date: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, pattern="^(P0|P1|P2|P3)$")
    assignee_id: Optional[int] = None
    due_date: Optional[str] = None


class UpdateStatusRequest(BaseModel):
    status: str = Field(..., pattern="^(todo|in_progress|done|archived)$")


class AddCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


@router.post("", summary="创建任务")
def create_task(
    req: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_member(db, req.project_id, current_user.id)

    # 如果指定了指派人，检查是否是项目成员
    if req.assignee_id:
        check_project_member(db, req.project_id, req.assignee_id)

    task = Task(
        project_id=req.project_id,
        title=req.title,
        description=req.description,
        priority=TaskPriority(req.priority),
        assignee_id=req.assignee_id,
        creator_id=current_user.id,
        due_date=datetime.fromisoformat(req.due_date) if req.due_date else None
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {"code": 200, "msg": "创建成功", "data": {"task_id": task.id, "title": task.title}}


@router.get("", summary="任务列表")
def list_tasks(
    project_id: int = Query(...),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_member(db, project_id, current_user.id)

    query = db.query(Task).filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)

    total = query.count()
    tasks = query.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "code": 200, "msg": "success",
        "data": {
            "total": total, "page": page, "page_size": page_size,
            "items": [{
                "id": t.id, "title": t.title, "status": t.status.value,
                "priority": t.priority.value, "assignee_id": t.assignee_id,
                "creator_id": t.creator_id, "due_date": str(t.due_date) if t.due_date else None,
                "created_at": str(t.created_at)
            } for t in tasks]
        }
    }


@router.get("/{task_id}", summary="任务详情")
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundError(msg="任务不存在")
    check_project_member(db, task.project_id, current_user.id)

    comments = db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at).all()
    comment_list = []
    for c in comments:
        user = db.query(User).filter(User.id == c.user_id).first()
        comment_list.append({
            "id": c.id, "user_id": c.user_id, "username": user.username,
            "content": c.content, "created_at": str(c.created_at)
        })

    return {
        "code": 200, "msg": "success",
        "data": {
            "id": task.id, "project_id": task.project_id, "title": task.title,
            "description": task.description, "status": task.status.value,
            "priority": task.priority.value, "assignee_id": task.assignee_id,
            "creator_id": task.creator_id, "due_date": str(task.due_date) if task.due_date else None,
            "comments": comment_list, "created_at": str(task.created_at), "updated_at": str(task.updated_at)
        }
    }


@router.put("/{task_id}", summary="更新任务")
def update_task(
    task_id: int,
    req: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundError(msg="任务不存在")
    check_project_member(db, task.project_id, current_user.id)

    if req.title is not None:
        task.title = req.title
    if req.description is not None:
        task.description = req.description
    if req.priority is not None:
        task.priority = TaskPriority(req.priority)
    if req.assignee_id is not None:
        if req.assignee_id:
            check_project_member(db, task.project_id, req.assignee_id)
        task.assignee_id = req.assignee_id
    if req.due_date is not None:
        task.due_date = datetime.fromisoformat(req.due_date) if req.due_date else None

    db.commit()
    return {"code": 200, "msg": "更新成功", "data": None}


@router.put("/{task_id}/status", summary="任务状态流转")
def update_task_status(
    task_id: int,
    req: UpdateStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundError(msg="任务不存在")
    check_project_member(db, task.project_id, current_user.id)

    new_status = TaskStatus(req.status)
    allowed = STATUS_TRANSITIONS.get(task.status, [])
    if new_status not in allowed:
        raise BizError(msg=f"状态不允许从 {task.status.value} 变更为 {new_status.value}，允许的目标状态：{[s.value for s in allowed]}")

    task.status = new_status
    db.commit()
    return {"code": 200, "msg": "状态更新成功", "data": {"task_id": task.id, "status": new_status.value}}


@router.delete("/{task_id}", summary="删除任务")
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundError(msg="任务不存在")

    # 只有创建者、项目管理员或项目创建者可以删除
    member = check_project_member(db, task.project_id, current_user.id)
    if task.creator_id != current_user.id and member.role.value not in ("owner", "admin"):
        raise ForbiddenError(msg="只有任务创建者或项目管理员可以删除任务")

    db.delete(task)
    db.commit()
    return {"code": 200, "msg": "删除成功", "data": None}


@router.post("/{task_id}/comments", summary="添加评论")
def add_comment(
    task_id: int,
    req: AddCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundError(msg="任务不存在")
    check_project_member(db, task.project_id, current_user.id)

    comment = TaskComment(task_id=task_id, user_id=current_user.id, content=req.content)
    db.add(comment)
    db.commit()
    return {"code": 200, "msg": "评论成功", "data": {"comment_id": comment.id}}


@router.get("/{task_id}/comments", summary="获取评论列表")
def list_comments(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundError(msg="任务不存在")
    check_project_member(db, task.project_id, current_user.id)

    comments = db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at).all()
    result = []
    for c in comments:
        user = db.query(User).filter(User.id == c.user_id).first()
        result.append({
            "id": c.id, "user_id": c.user_id, "username": user.username,
            "content": c.content, "created_at": str(c.created_at)
        })

    return {"code": 200, "msg": "success", "data": result}
