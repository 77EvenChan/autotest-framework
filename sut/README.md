# TaskFlow - 任务流管理平台

一个轻量级的项目管理后端，支持团队协作、任务管理、项目管理、数据统计。

## 技术栈

- Python 3.13 + FastAPI
- MySQL 8.0 + SQLAlchemy 2.0
- Redis 7（缓存 + 登录限制）
- JWT Token 认证

## 快速启动

1. 确保 MySQL 和 Redis 已启动（docker compose up -d）
2. 安装依赖：`pip install -r requirements.txt`
3. 启动服务：`uvicorn app.main:app --reload --port 8000`
4. 访问 Swagger 文档：http://localhost:8000/docs

## 接口列表

### 认证
- POST /api/auth/register — 注册
- POST /api/auth/login — 登录
- POST /api/auth/refresh — 刷新Token

### 用户
- GET /api/users/me — 获取当前用户信息
- PUT /api/users/me — 更新个人信息

### 项目管理
- POST /api/projects — 创建项目
- GET /api/projects — 项目列表（分页、筛选）
- GET /api/projects/{id} — 项目详情
- PUT /api/projects/{id} — 更新项目
- DELETE /api/projects/{id} — 删除项目
- POST /api/projects/{id}/members — 添加成员
- DELETE /api/projects/{id}/members/{uid} — 移除成员

### 任务管理
- POST /api/tasks — 创建任务
- GET /api/tasks — 任务列表（按项目/状态/优先级/指派人筛选）
- GET /api/tasks/{id} — 任务详情
- PUT /api/tasks/{id} — 更新任务
- PUT /api/tasks/{id}/status — 任务状态流转
- DELETE /api/tasks/{id} — 删除任务
- POST /api/tasks/{id}/comments — 添加评论
- GET /api/tasks/{id}/comments — 评论列表

### 数据统计
- GET /api/stats/project/{id} — 项目统计（任务数、完成率、优先级分布）
- GET /api/stats/user/{id} — 用户统计（参与项目数、任务完成率）

## 状态流转规则

```
todo → in_progress → done → archived
         ↑              ↓
         └──────────────┘
```

## 数据库表

- users — 用户表
- projects — 项目表
- project_members — 项目成员关联表
- tasks — 任务表
- task_comments — 任务评论表
