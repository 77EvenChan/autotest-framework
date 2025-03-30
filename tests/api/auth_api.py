from tests.api.base_api import BaseApi


class AuthApi(BaseApi):
    """认证接口封装"""

    def register(self, username: str, password: str, email: str):
        return self.post("/api/auth/register", {
            "username": username, "password": password, "email": email
        })

    def login(self, username: str, password: str):
        return self.post("/api/auth/login", {
            "username": username, "password": password
        })

    def refresh(self, refresh_token: str):
        return self.post("/api/auth/refresh", {"refresh_token": refresh_token})

    def login_and_set_token(self, username: str, password: str) -> dict:
        """登录并自动设置 Token，返回响应数据"""
        resp = self.login(username, password)
        data = resp.json()
        self.set_token(data["access_token"])
        return data