import json
import requests
from tests.config.config_loader import load_config
from tests.config.logger import setup_logger

logger = setup_logger()


class BaseApi:
    """HTTP 请求封装基类 — 所有接口类的父类"""

    def __init__(self):
        cfg = load_config()
        self.base_url = cfg["base_url"]
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def set_token(self, token: str):
        """设置认证 Token，后续请求自动带上"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get(self, path: str, params: dict = None, **kwargs) -> requests.Response:
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, json_data: dict = None, **kwargs) -> requests.Response:
        return self._request("POST", path, json_data=json_data, **kwargs)

    def put(self, path: str, json_data: dict = None, **kwargs) -> requests.Response:
        return self._request("PUT", path, json_data=json_data, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self._request("DELETE", path, **kwargs)

    def _request(self, method: str, path: str, json_data=None, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"

        # 请求日志
        logger.info(f"[{method}] {path}")
        if json_data:
            # 密码不打印
            safe_data = {k: ("***" if k == "password" else v) for k, v in json_data.items()}
            logger.info(f"请求体: {json.dumps(safe_data, ensure_ascii=False)}")

        resp = self.session.request(method, url, json=json_data, **kwargs)

        # 响应日志
        logger.info(f"响应: {resp.status_code} | {resp.text[:200]}")
        return resp

    def assert_success(self, resp: requests.Response, expected_code: int = 200):
        """断言接口返回成功"""
        actual = resp.json().get("code")
        assert actual == expected_code, \
            f"期望 code={expected_code}，实际 code={actual}，响应: {resp.text}"

    def assert_biz_error(self, resp: requests.Response, expected_msg: str = None):
        """断言接口返回业务错误（code != 200）"""
        data = resp.json()
        assert data.get("code") != 200, f"期望业务错误，但返回成功: {resp.text}"
        if expected_msg:
            assert expected_msg in data.get("msg", ""), \
                f"期望 msg 包含 '{expected_msg}'，实际: {data.get('msg')}"