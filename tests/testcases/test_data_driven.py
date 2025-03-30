"""数据驱动测试用例 — 从 YAML 文件读取测试数据，自动展开为多条用例

覆盖接口：注册、登录、创建任务、状态流转
数据来源：tests/data/*.yaml
加载工具：tests/utils/yaml_loader.py
"""
import time
import pytest
import allure
from tests.api.auth_api import AuthApi
from tests.api.task_api import TaskApi
from tests.utils.yaml_loader import load_yaml
from tests.config.config_loader import load_config


@pytest.fixture(autouse=True)
def _clear_login_locks():
    """每个测试前清除登录锁定和全局限流，防止数据驱动测试间互相影响"""
    try:
        import redis as redis_lib
        cfg = load_config()
        r = redis_lib.Redis(
            host=cfg["redis"]["host"], port=cfg["redis"]["port"],
            password=cfg["redis"]["password"], decode_responses=True
        )
        # 清除测试账号的登录锁定
        for user in [cfg["admin"]["username"], cfg["member"]["username"]]:
            r.delete(f"login_lock:{user}")
            r.delete(f"login_attempts:{user}")
        # 清除可能的全局登录限流键
        for key in r.scan_iter("login_*"):
            r.delete(key)
        r.close()
    except Exception:
        pass
    yield


def _make_unique(cases: list) -> list:
    """给每条用例的 username/email 加时间戳，避免重复注册冲突

    跳过：testadmin、空用户名、过短用户名（<=2字符，用于测试长度校验）
    """
    ts = int(time.time())
    for case in cases:
        username = case.get("username", "")
        if username and username != "testadmin" and len(username) > 2:
            case["username"] = f"{username}_{ts}"
        if case.get("email") and "@" in case["email"]:
            case["email"] = case["email"].replace("@", f"_{ts}@")
    return cases


# 模块加载时一次性读取并处理数据（避免每条用例重复读文件）
_register_cases = _make_unique(load_yaml("register_cases.yaml"))
_login_cases = load_yaml("login_cases.yaml")
_task_cases = load_yaml("task_create_cases.yaml")
_flow_cases = load_yaml("status_flow_cases.yaml")


# ─────────────────────────────────────────────
# 注册接口 — 数据驱动
# ─────────────────────────────────────────────

@allure.epic("认证模块")
@allure.feature("注册接口-数据驱动")
class TestRegisterDataDriven:

    @pytest.mark.parametrize(
        "case_id,title,username,password,email,expected_code,expected_msg_contains",
        [(c["case_id"], c["title"], c["username"], c["password"],
          c["email"], c["expected_code"], c["expected_msg_contains"])
         for c in _register_cases]
    )
    def test_register(self, case_id, title, username, password, email,
                      expected_code, expected_msg_contains):
        """注册接口数据驱动测试"""
        allure.dynamic.title(f"[{case_id}] {title}")

        api = AuthApi()
        resp = api.register(username, password, email)

        if expected_code == 422:
            # FastAPI Pydantic 校验返回 422，没有 code 字段
            assert resp.status_code == 422
        else:
            data = resp.json()
            assert data["code"] == expected_code
            if expected_msg_contains:
                assert expected_msg_contains in data["msg"]


# ─────────────────────────────────────────────
# 登录接口 — 数据驱动
# ─────────────────────────────────────────────

@allure.epic("认证模块")
@allure.feature("登录接口-数据驱动")
class TestLoginDataDriven:

    @pytest.mark.parametrize(
        "case_id,title,username,password,expected_code,expected_has_token",
        [(c["case_id"], c["title"], c["username"], c["password"],
          c["expected_code"], c["expected_has_token"])
         for c in _login_cases]
    )
    def test_login(self, case_id, title, username, password,
                   expected_code, expected_has_token):
        """登录接口数据驱动测试"""
        allure.dynamic.title(f"[{case_id}] {title}")

        api = AuthApi()
        resp = api.login(username, password)

        if expected_code == 422:
            assert resp.status_code == 422
        elif expected_code == 200:
            data = resp.json()
            assert "access_token" in data
            assert "refresh_token" in data
        else:
            data = resp.json()
            # 接受 400（业务错误）或 429（限流）都算登录失败
            assert data["code"] in (expected_code, 429)
            assert "access_token" not in data


# ─────────────────────────────────────────────
# 创建任务 — 数据驱动
# ─────────────────────────────────────────────

@allure.epic("任务模块")
@allure.feature("创建任务-数据驱动")
class TestCreateTaskDataDriven:

    @pytest.mark.parametrize(
        "case_id,title,task_title,priority,description,expected_code",
        [(c["case_id"], c["title"], c["task_title"], c["priority"],
          c["description"], c["expected_code"])
         for c in _task_cases]
    )
    def test_create_task(self, case_id, title, task_title, priority,
                         description, expected_code, task_api, test_project):
        """创建任务数据驱动测试"""
        allure.dynamic.title(f"[{case_id}] {title}")

        data = {
            "project_id": test_project,
            "title": task_title,
            "priority": priority,
            "description": description
        }
        resp = task_api.post("/api/tasks", data)

        if expected_code == 422:
            assert resp.status_code == 422
        else:
            result = resp.json()
            assert result["code"] == expected_code


# ─────────────────────────────────────────────
# 状态流转 — 数据驱动
# ─────────────────────────────────────────────

@allure.epic("任务模块")
@allure.feature("状态流转-数据驱动")
class TestStatusFlowDataDriven:

    @pytest.mark.parametrize(
        "case_id,title,from_status,to_status,expected_code",
        [(c["case_id"], c["title"], c["from_status"], c["to_status"],
          c["expected_code"])
         for c in _flow_cases]
    )
    def test_status_flow(self, case_id, title, from_status, to_status,
                         expected_code, task_api, test_project):
        """任务状态流转数据驱动测试"""
        allure.dynamic.title(f"[{case_id}] {title}")

        # 创建一个新任务（初始状态 todo）
        create_resp = task_api.create(test_project, f"流转测试_{case_id}")
        task_id = create_resp.json()["data"]["task_id"]

        # 如果需要先流转到 from_status（非 todo），先执行中间步骤
        if from_status == "in_progress":
            task_api.update_status(task_id, "in_progress")
        elif from_status == "done":
            task_api.update_status(task_id, "in_progress")
            task_api.update_status(task_id, "done")
        elif from_status == "archived":
            task_api.update_status(task_id, "in_progress")
            task_api.update_status(task_id, "done")
            task_api.update_status(task_id, "archived")

        # 执行目标流转
        resp = task_api.update_status(task_id, to_status)
        data = resp.json()

        assert data["code"] == expected_code
