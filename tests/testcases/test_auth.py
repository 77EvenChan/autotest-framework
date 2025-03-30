"""认证接口测试用例 — 注册/登录/Token刷新"""
import pytest
import allure
from tests.api.auth_api import AuthApi


@allure.epic("认证模块")
@allure.feature("注册接口")
class TestRegister:
    """注册接口 POST /api/auth/register"""

    def test_register_success(self):
        """正常注册"""
        import time
        username = f"testuser_{int(time.time())}"
        api = AuthApi()
        resp = api.register(username, "Test@123", f"{username}@test.com")
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["username"] == username

    def test_register_duplicate_username(self, admin_api):
        """用户名已存在"""
        api = AuthApi()
        resp = api.register("testadmin", "Test@123", "new@test.com")
        data = resp.json()

        assert data["code"] != 200
        assert "已存在" in data["msg"]

    def test_register_invalid_email(self):
        """邮箱格式错误"""
        api = AuthApi()
        resp = api.register("newuser123", "Test@123", "not-an-email")
        data = resp.json()

        assert data["code"] != 200
        assert "邮箱" in data["msg"]

    def test_register_short_password(self):
        """密码太短"""
        import time
        api = AuthApi()
        ts = int(time.time())
        resp = api.register(f"short_{ts}", "123", f"short_{ts}@test.com")

        assert resp.status_code != 200  # FastAPI参数校验返回422，格式是{"detail": [...]}

    def test_register_invalid_username_chars(self):
        """用户名包含特殊字符"""
        api = AuthApi()
        resp = api.register("user@#$", "Test@123", "bad@test.com")
        data = resp.json()

        assert data["code"] != 200
        assert "字母" in data["msg"] or "下划线" in data["msg"]


@allure.epic("认证模块")
@allure.feature("登录接口")
class TestLogin:
    """登录接口 POST /api/auth/login"""

    def test_login_success(self, admin_api):
        """正常登录"""
        api = AuthApi()
        resp = api.login("testadmin", "Test@123456")
        data = resp.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """密码错误"""
        api = AuthApi()
        resp = api.login("testadmin", "wrong_password")
        data = resp.json()

        assert data["code"] != 200
        assert "密码" in data["msg"] or "错误" in data["msg"]

    def test_login_nonexistent_user(self):
        """用户不存在"""
        api = AuthApi()
        resp = api.login("ghost_user_xyz", "Test@123")
        data = resp.json()

        assert data["code"] != 200

    def test_login_and_set_token(self):
        """登录并设置Token，后续请求自动带上"""
        api = AuthApi()
        result = api.login_and_set_token("testadmin", "Test@123456")

        assert "access_token" in result
        # 验证Token已生效：调用需要认证的接口
        me_resp = api.get("/api/users/me")
        me_data = me_resp.json()
        assert me_resp.status_code == 200
        assert me_data.get("username") == "testadmin"


@allure.epic("认证模块")
@allure.feature("Token刷新")
class TestRefreshToken:
    """刷新Token接口 POST /api/auth/refresh"""

    def test_refresh_success(self):
        """正常刷新"""
        api = AuthApi()
        login_data = api.login("testadmin", "Test@123456").json()
        refresh_token = login_data["refresh_token"]

        resp = api.refresh(refresh_token)
        data = resp.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_with_invalid_token(self):
        """无效Token刷新"""
        api = AuthApi()
        resp = api.refresh("this_is_a_fake_token")
        data = resp.json()

        assert data["code"] != 200

    def test_refresh_with_access_token(self):
        """用access_token当refresh_token刷新（应该失败）"""
        api = AuthApi()
        login_data = api.login("testadmin", "Test@123456").json()
        access_token = login_data["access_token"]

        resp = api.refresh(access_token)
        data = resp.json()

        assert data["code"] != 200
        assert "类型" in data["msg"] or "refresh" in data["msg"].lower()
