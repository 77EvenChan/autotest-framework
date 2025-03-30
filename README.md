# TaskFlow 自动化测试框架

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-7.4+-green?logo=pytest&logoColor=white)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-black?logo=githubactions&logoColor=white)

通用接口自动化测试框架，基于 pytest + requests 构建，配套 TaskFlow 任务管理 API 作为被测服务。支持数据驱动、Allure 报告、Docker 一键部署。

---

## 技术栈

| 类别 | 技术 |
|------|------|
| 测试框架 | pytest、requests、PyYAML |
| 测试报告 | allure-pytest |
| 被测服务 | FastAPI、MySQL 8.0、Redis 7 |
| 容器化 | Docker、Docker Compose |
| CI/CD | GitHub Actions、Jenkins |

---

## 目录结构

```
autotest-framework/
├── .github/workflows/          # GitHub Actions
├── sut/                        # 被测服务（TaskFlow API）
│   ├── app/
│   │   ├── routes/             # auth / projects / tasks / stats
│   │   ├── models/
│   │   └── main.py
│   └── requirements.txt
├── tests/
│   ├── api/                    # 接口封装层
│   ├── config/                 # 配置 + 日志
│   ├── data/                   # YAML 测试数据
│   ├── testcases/              # 测试用例
│   ├── utils/                  # 工具类
│   └── conftest.py             # 全局 fixture
├── scripts/                    # 运行脚本
├── Jenkinsfile
├── Dockerfile
├── docker-compose.yml
├── docker-compose.ci.yml
├── requirements.txt
└── pyproject.toml
```

---

## 快速开始

```bash
# 1. 安装依赖
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# 2. 启动服务
docker-compose up -d
cd sut && pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. 运行测试
python -m pytest tests/ -v
```

生成 Allure 报告：

```bash
python -m pytest tests/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

---

## 测试覆盖

| 模块 | 接口 | 用例数 |
|------|------|--------|
| 认证 | 注册 / 登录 / Token刷新 | 12 |
| 项目管理 | CRUD / 成员 / 权限 | 16 |
| 任务管理 | CRUD / 状态流转 / 评论 | 22 |
| 数据统计 | 项目统计 / 用户统计 | 4 |
| 数据驱动 | YAML 参数化用例 | 26 |

---

## CI/CD

**GitHub Actions**：push 或 PR 到 main 自动运行测试，JUnit 报告作为 Artifact 上传。

**Jenkins**：Pipeline 5 阶段（拉代码 → 装依赖 → 启服务 → 跑测试 → 出报告）。

**Docker**：`docker-compose -f docker-compose.ci.yml up --build` 一键拉起全部环境并执行测试。

---

## License

MIT
