import pytest
import allure
from tests.api.auth_api import AuthApi
from tests.api.project_api import ProjectApi
from tests.api.task_api import TaskApi
from tests.api.stats_api import StatsApi
from tests.config.config_loader import load_config


def pytest_configure(config):
    """注册 Allure 环境信息"""
    config.option.allure_report_dir = "reports/allure-results"


@pytest.fixture(scope="session", autouse=True)
def ensure_test_users():
    """确保测试账号存在并可登录 — 整个测试会话只执行一次"""
    import redis as redis_lib
    api = AuthApi()
    cfg = load_config()

    # 清除可能存在的登录锁定（之前测试失败可能导致账号被锁）
    try:
        r = redis_lib.Redis(
            host=cfg["redis"]["host"], port=cfg["redis"]["port"],
            password=cfg["redis"]["password"], decode_responses=True
        )
        r.delete(f"login_lock:{cfg['admin']['username']}")
        r.delete(f"login_attempts:{cfg['admin']['username']}")
        r.delete(f"login_lock:{cfg['member']['username']}")
        r.delete(f"login_attempts:{cfg['member']['username']}")
        r.close()
    except Exception:
        pass  # Redis连不上就跳过，不影响注册

    # 注册管理员账号（已存在就忽略返回的错误）
    api.register(cfg["admin"]["username"], cfg["admin"]["password"],
                 f"{cfg['admin']['username']}@test.com")

    # 注册普通成员账号
    api.register(cfg["member"]["username"], cfg["member"]["password"],
                 f"{cfg['member']['username']}@test.com")

    yield


@pytest.fixture(scope="session")
def admin_api(ensure_test_users):
    """管理员 API 客户端 — 整个测试会话只创建一次，所有测试共享"""
    api = AuthApi()
    cfg = load_config()
    api.login_and_set_token(cfg["admin"]["username"], cfg["admin"]["password"])
    yield api


@pytest.fixture(scope="session")
def member_api(ensure_test_users):
    """普通成员 API 客户端"""
    api = AuthApi()
    cfg = load_config()
    api.login_and_set_token(cfg["member"]["username"], cfg["member"]["password"])
    yield api


@pytest.fixture
def project_api(admin_api):
    """项目接口 — 依赖 admin_api，自动拿到已登录的 session"""
    api = ProjectApi()
    api.session = admin_api.session  # 复用管理员的登录态
    yield api


@pytest.fixture
def task_api(admin_api):
    """任务接口 — 依赖 admin_api"""
    api = TaskApi()
    api.session = admin_api.session
    yield api


@pytest.fixture
def stats_api(admin_api):
    """统计接口 — 依赖 admin_api"""
    api = StatsApi()
    api.session = admin_api.session
    yield api


@pytest.fixture
def test_project(project_api):
    """创建一个测试项目，测试结束后自动删除"""
    import time
    resp = project_api.create(f"测试项目_{int(time.time())}", "用于自动化测试")
    data = resp.json()
    project_id = data["data"]["project_id"]
    yield project_id
    # teardown：清理测试数据
    project_api.delete_project(project_id)


@pytest.fixture
def test_task(task_api, test_project):
    """创建一个测试任务，测试结束后自动删除"""
    resp = task_api.create(test_project, "测试任务_自动化")
    data = resp.json()
    task_id = data["data"]["task_id"]
    yield task_id
    task_api.delete_task(task_id)