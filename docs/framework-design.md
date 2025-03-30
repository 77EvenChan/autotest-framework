# TaskFlow 自动化测试框架 — 架构设计文档

> 版本：1.0  |  更新日期：2025-02  |  维护人：陈工

---

## 1. 设计目标

| 目标 | 说明 |
|------|------|
| 分层解耦 | 接口封装、测试用例、数据、配置四层独立，改一层不影响其他层 |
| 数据驱动 | 测试数据外置到 YAML，不硬编码在代码中 |
| 环境可切换 | 通过配置文件切换 dev/staging/prod 环境 |
| 报告可视化 | 集成 Allure，测试结果可按模块/接口/用例查看 |
| CI/CD 友好 | 一键 Docker 部署，支持 GitHub Actions 和 Jenkins |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    测试用例层 (testcases/)                │
│   test_auth.py   test_project.py   test_task.py          │
│   test_stats.py   test_data_driven.py                    │
├─────────────────────────────────────────────────────────┤
│                    接口封装层 (api/)                      │
│   base_api.py → auth_api.py / project_api.py            │
│                → task_api.py / stats_api.py              │
├─────────────────────────────────────────────────────────┤
│                    数据层 (data/)                        │
│   register_cases.yaml   login_cases.yaml                 │
│   task_create_cases.yaml   status_flow_cases.yaml        │
├─────────────────────────────────────────────────────────┤
│                    配置层 (config/)                      │
│   config.yaml   config_loader.py   logger.py             │
├─────────────────────────────────────────────────────────┤
│                    工具层 (utils/)                       │
│   yaml_loader.py                                        │
├─────────────────────────────────────────────────────────┤
│                    全局控制 (conftest.py)                 │
│   fixture 管理 / 测试账号初始化 / Redis清理               │
└─────────────────────────────────────────────────────────┘
```

**调用关系**：测试用例 → 接口封装层 → requests → 被测服务（TaskFlow API）

---

## 3. 各层详细设计

### 3.1 接口封装层（api/）

**设计思路**：用继承消除重复代码。BaseApi 封装通用 HTTP 操作，各业务接口类继承 BaseApi 只写业务方法。

```
BaseApi（基类）
├── __init__()      # 创建 Session，设置通用请求头
├── set_token()     # 设置 JWT Token
├── get/post/put/delete()  # HTTP 方法封装
├── _request()      # 统一请求逻辑（日志、错误处理）
├── assert_success()      # 断言成功响应
└── assert_biz_error()    # 断言业务错误

AuthApi（认证接口）
├── register()           # 用户注册
├── login()              # 用户登录
├── login_and_set_token()  # 登录并设置 Token（一步到位）
└── refresh_token()      # 刷新 Token

ProjectApi（项目接口）
├── create()             # 创建项目
├── get_detail()         # 获取项目详情
├── list()               # 项目列表
├── update()             # 更新项目
├── delete_project()     # 删除项目（不能命名为 delete，会与父类冲突）
└── add_member()         # 添加成员

TaskApi（任务接口）
├── create()             # 创建任务
├── get_detail()         # 获取任务详情
├── update()             # 更新任务
├── update_status()      # 更新任务状态
├── delete_task()        # 删除任务
└── add_comment()        # 添加评论
```

**关键设计决策**：
- 方法命名不能与 BaseApi 的 get/post/put/delete 同名，否则子类调用时会递归
- Session 复用：project_api 复用 admin_api.session，避免重复登录
- Token 管理：登录成功后通过 set_token() 自动附加到后续请求

### 3.2 数据层（data/）

采用 YAML 文件存储测试数据，支持参数化测试：

```yaml
# register_cases.yaml 示例
cases:
  - id: REG_001
    username: "normal_user"
    password: "pass123456"
    email: "normal@test.com"
    expected_code: 200
    description: "正常注册"

  - id: REG_002
    username: ""
    password: "pass123456"
    email: "empty@test.com"
    expected_code: 422
    description: "用户名为空"
```

**YAML 加载器**（yaml_loader.py）：
- `load_yaml(file_name)` — 加载 YAML 文件，返回用例列表
- `parametrize_from_yaml(file_name)` — 转换为 pytest.mark.parametrize 可用的参数

### 3.3 配置层（config/）

```
config.yaml        ← 环境配置（base_url、数据库、Redis、测试账号）
config_loader.py   ← 配置加载器（带全局缓存，只读一次文件）
logger.py          ← 日志配置（文件+控制台双输出）
```

**config.yaml 结构**：
```yaml
base_url: "http://localhost:8000"
admin:
  username: "testadmin"
  password: "admin123"
member:
  username: "testmember"
  password: "member123"
redis:
  host: "localhost"
  port: 6379
  password: "redis123"
```

### 3.4 全局控制层（conftest.py）

pytest 的 conftest.py 是框架的核心控制文件，负责：

| Fixture | Scope | 职责 |
|---------|-------|------|
| ensure_test_users | session | 确保测试账号存在，清理 Redis 登录锁 |
| admin_api | session | 管理员登录，全会话共享 |
| member_api | session | 普通成员登录，全会话共享 |
| project_api | function | 项目接口客户端（复用 admin_api.session） |
| task_api | function | 任务接口客户端 |
| test_project | function | 创建临时测试项目，用完自动删除 |
| test_task | function | 创建临时测试任务，用完自动删除 |

**Fixture 依赖链**：
```
test_task → task_api → admin_api → ensure_test_users
         → test_project → project_api → admin_api → ensure_test_users
```

### 3.5 测试用例层（testcases/）

| 文件 | 覆盖模块 | 用例数 |
|------|---------|--------|
| test_auth.py | 注册/登录/Token刷新 | 12 |
| test_project.py | 项目CRUD/成员/权限 | 16 |
| test_task.py | 任务CRUD/状态流转/评论 | 22 |
| test_stats.py | 项目统计/用户统计 | 4 |
| test_data_driven.py | YAML参数化用例 | 26 |

**用例组织方式**：
- 按接口模块分文件
- 按接口方法分 class（如 TestCreateTask、TestUpdateTask）
- 每个测试方法只测一个场景
- 异常用例绕过封装层，直接发原始请求（精确控制请求体）

---

## 4. 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 测试框架 | pytest | 插件生态丰富，fixture 机制强大 |
| HTTP 客户端 | requests + Session | 自动管理 Cookie/Headers，减少重复代码 |
| 数据驱动 | YAML + parametrize | 数据与代码分离，非技术人员也能维护用例 |
| 测试报告 | allure-pytest | 支持按模块/接口/用例多维度查看结果 |
| 被测服务 | FastAPI + SQLAlchemy | 自动生成 OpenAPI 文档，方便接口验证 |
| 数据库 | MySQL 8.0 | 企业常用，兼容性好 |
| 缓存 | Redis 7 | 用于登录限流、Session 缓存 |
| 容器化 | Docker + docker-compose | 环境一致性，一键部署 |
| CI/CD | GitHub Actions + Jenkins | 覆盖云+本地两种 CI 场景 |

---

## 5. 数据流

### 5.1 一次测试的完整数据流

```
1. conftest.py 加载配置 → config.yaml
2. ensure_test_users 注册测试账号 → SUT /api/auth/register
3. admin_api 登录获取 Token → SUT /api/auth/login
4. 测试用例调用接口封装层 → base_api.py 发 HTTP 请求
5. SUT 处理请求 → MySQL/Redis 读写
6. 返回响应 → 测试用例断言
7. conftest.py teardown 清理数据 → 调用 delete 接口
8. allure 记录测试结果 → reports/allure-results/
```

### 5.2 数据驱动测试流程

```
1. YAML 文件定义测试数据（data/register_cases.yaml）
2. yaml_loader.py 加载并解析 YAML
3. @pytest.mark.parametrize 参数化测试方法
4. pytest 为每组参数生成独立的测试用例
5. 每个用例独立执行、独立断言、独立报告
```

---

## 6. 扩展点

| 扩展方向 | 改动范围 | 说明 |
|----------|---------|------|
| 新增接口模块 | api/ + testcases/ | 新建 XxxApi 继承 BaseApi，新建 test_xxx.py |
| 新增测试环境 | config/config.yaml | 添加新的环境配置段 |
| 切换数据源 | data/*.yaml | 修改 YAML 文件即可，不改代码 |
| 接入新的报告 | conftest.py + pyproject.toml | 替换或并行添加报告插件 |
| 添加 UI 测试 | 新增 ui/ 目录 | 引入 Playwright，与现有框架并行 |

---

## 7. CI/CD 集成

### 7.1 GitHub Actions

- 触发条件：push 或 PR 到 main 分支
- 服务容器：MySQL 8.0 + Redis 7（Docker services）
- 缓存策略：pip 缓存依赖，加速构建
- 产物：JUnit XML 报告作为 Artifact 上传

### 7.2 Jenkins Pipeline

```
Stage 1: 拉代码（git checkout）
Stage 2: 装依赖（pip install）
Stage 3: 启服务（docker-compose up）
Stage 4: 跑测试（pytest + Allure）
Stage 5: 出报告（Allure Report）
```

### 7.3 Docker Compose（CI 模式）

```yaml
services:
  mysql      → 健康检查 → 就绪后启动
  redis      → 健康检查 → 就绪后启动
  sut        → 依赖 mysql/redis 健康 → 启动被测服务
  test-runner → 依赖 sut 健康 → 执行测试 → 挂载报告到宿主机
```

**关键设计**：depends_on + healthcheck 确保服务真正可用后才启动下游，避免"容器启动但服务未就绪"的问题。
