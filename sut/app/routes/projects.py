from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectMember, ProjectStatus, MemberRole
from app.middleware.auth import get_current_user
from app.utils.exceptions import BizError, NotFoundError, ForbiddenError

router = APIRouter(prefix="/api/projects", tags=["项目管理"])


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class AddMemberRequest(BaseModel):
    username: str
    role: str = Field("member", pattern="^(admin|member)$")


def check_project_member(db: Session, project_id: int, user_id: int) -> ProjectMember:
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    if not member:
        raise ForbiddenError(msg="你不是该项目的成员")
    return member


@router.post("", summary="创建项目")
def create_project(
    req: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 项目名称唯一性（同一用户下）
    existing = db.query(Project).filter(
        Project.name == req.name, Project.owner_id == current_user.id
    ).first()
    if existing:
        raise BizError(msg="你已创建过同名项目")

    project = Project(name=req.name, description=req.description, owner_id=current_user.id)
    db.add(project)
    db.flush()

    # 创建者自动成为 owner
    member = ProjectMember(project_id=project.id, user_id=current_user.id, role=MemberRole.OWNER)
    db.add(member)
    db.commit()
    db.refresh(project)

    return {"code": 200, "msg": "创建成功", "data": {"project_id": project.id, "name": project.name}}


@router.get("", summary="项目列表")
def list_projects(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 只查用户参与的项目
    query = db.query(Project).join(ProjectMember).filter(
        ProjectMember.user_id == current_user.id
    )
    if status:
        query = query.filter(Project.status == status)

    total = query.count()
    projects = query.order_by(Project.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "code": 200, "msg": "success",
        "data": {
            "total": total, "page": page, "page_size": page_size,
            "items": [{"id": p.id, "name": p.name, "description": p.description,
                        "status": p.status.value, "created_at": str(p.created_at)} for p in projects]
        }
    }


@router.get("/{project_id}", summary="项目详情")
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_project_member(db, project_id, current_user.id)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError(msg="项目不存在")

    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    member_list = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        member_list.append({"user_id": m.user_id, "username": user.username, "role": m.role.value})

    return {
        "code": 200, "msg": "success",
        "data": {
            "id": project.id, "name": project.name, "description": project.description,
            "status": project.status.value, "owner_id": project.owner_id,
            "members": member_list, "created_at": str(project.created_at)
        }
    }


@router.put("/{project_id}", summary="更新项目")
def update_project(
    project_id: int,
    req: UpdateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = check_project_member(db, project_id, current_user.id)
    if member.role not in (MemberRole.OWNER, MemberRole.ADMIN):
        raise ForbiddenError(msg="只有管理员或创建者可以修改项目")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError(msg="项目不存在")

    if req.name is not None:
        project.name = req.name
    if req.description is not None:
        project.description = req.description

    db.commit()
    return {"code": 200, "msg": "更新成功", "data": None}


@router.delete("/{project_id}", summary="删除项目")
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = check_project_member(db, project_id, current_user.id)
    if member.role != MemberRole.OWNER:
        raise ForbiddenError(msg="只有创建者可以删除项目")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise NotFoundError(msg="项目不存在")

    db.delete(project)
    db.commit()
    return {"code": 200, "msg": "删除成功", "data": None}


@router.post("/{project_id}/members", summary="添加项目成员")
def add_member(
    project_id: int,
    req: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = check_project_member(db, project_id, current_user.id)
    if member.role not in (MemberRole.OWNER, MemberRole.ADMIN):
        raise ForbiddenError(msg="只有管理员或创建者可以添加成员")

    target_user = db.query(User).filter(User.username == req.username).first()
    if not target_user:
        raise NotFoundError(msg=f"用户 {req.username} 不存在")

    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id, ProjectMember.user_id == target_user.id
    ).first()
    if existing:
        raise BizError(msg="该用户已是项目成员")

    new_member = ProjectMember(
        project_id=project_id, user_id=target_user.id, role=MemberRole(req.role)
    )
    db.add(new_member)
    db.commit()
    return {"code": 200, "msg": "添加成功", "data": None}


@router.delete("/{project_id}/members/{user_id}", summary="移除项目成员")
def remove_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = check_project_member(db, project_id, current_user.id)
    if member.role not in (MemberRole.OWNER, MemberRole.ADMIN):
        raise ForbiddenError(msg="只有管理员或创建者可以移除成员")

    target = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
    ).first()
    if not target:
        raise NotFoundError(msg="该用户不是项目成员")
    if target.role == MemberRole.OWNER:
        raise BizError(msg="不能移除项目创建者")

    db.delete(target)
    db.commit()
    return {"code": 200, "msg": "移除成功", "data": None}
