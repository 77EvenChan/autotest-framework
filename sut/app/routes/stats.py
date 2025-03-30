from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.task import Task, TaskStatus
from app.routes.projects import check_project_member
from app.middleware.auth import get_current_user
from app.utils.redis_client import redis_client
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/api/stats", tags=["数据统计"])


@router.get("/project/{project_id}", summary="项目统计")
def project_stats(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_member(db, project_id, current_user.id)

    # 先查缓存
    cache_key = f"stats:project:{project_id}"
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return {"code": 200, "msg": "success", "data": json.loads(cached), "from_cache": True}

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError(msg="项目不存在")

    total_tasks = db.query(func.count(Task.id)).filter(Task.project_id == project_id).scalar() or 0
    done_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id, Task.status == TaskStatus.DONE
    ).scalar() or 0
    todo_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id, Task.status == TaskStatus.TODO
    ).scalar() or 0
    in_progress_tasks = db.query(func.count(Task.id)).filter(
        Task.project_id == project_id, Task.status == TaskStatus.IN_PROGRESS
    ).scalar() or 0

    completion_rate = round(done_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0.0

    # 按优先级统计
    priority_stats = {}
    for p in ["P0", "P1", "P2", "P3"]:
        count = db.query(func.count(Task.id)).filter(
            Task.project_id == project_id, Task.priority == p
        ).scalar() or 0
        priority_stats[p] = count

    result = {
        "project_id": project_id,
        "project_name": project.name,
        "total_tasks": total_tasks,
        "todo": todo_tasks,
        "in_progress": in_progress_tasks,
        "done": done_tasks,
        "completion_rate": completion_rate,
        "priority_distribution": priority_stats
    }

    # 写入缓存，TTL 5分钟
    import json
    redis_client.setex(cache_key, 300, json.dumps(result, ensure_ascii=False))

    return {"code": 200, "msg": "success", "data": result}


@router.get("/user/{user_id}", summary="用户统计")
def user_stats(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 先查缓存
    cache_key = f"stats:user:{user_id}"
    cached = redis_client.get(cache_key)
    if cached:
        import json
        return {"code": 200, "msg": "success", "data": json.loads(cached), "from_cache": True}

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError(msg="用户不存在")

    # 参与的项目数
    project_count = db.query(func.count(ProjectMember.id)).filter(
        ProjectMember.user_id == user_id
    ).scalar() or 0

    # 创建的任务数
    created_tasks = db.query(func.count(Task.id)).filter(Task.creator_id == user_id).scalar() or 0

    # 被指派的任务数
    assigned_tasks = db.query(func.count(Task.id)).filter(Task.assignee_id == user_id).scalar() or 0

    # 被指派且已完成的任务数
    assigned_done = db.query(func.count(Task.id)).filter(
        Task.assignee_id == user_id, Task.status == TaskStatus.DONE
    ).scalar() or 0

    completion_rate = round(assigned_done / assigned_tasks * 100, 1) if assigned_tasks > 0 else 0.0

    result = {
        "user_id": user_id,
        "username": user.username,
        "project_count": project_count,
        "created_tasks": created_tasks,
        "assigned_tasks": assigned_tasks,
        "assigned_done": assigned_done,
        "completion_rate": completion_rate
    }

    import json
    redis_client.setex(cache_key, 300, json.dumps(result, ensure_ascii=False))

    return {"code": 200, "msg": "success", "data": result}
