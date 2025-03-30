"""数据统计接口测试用例"""
import pytest
from tests.api.task_api import TaskApi


class TestProjectStats:
    """项目统计 GET /api/stats/project/{id}"""

    def test_project_stats_success(self, stats_api, test_project, task_api):
        """正常获取项目统计（有数据）"""
        # 先造几条任务数据
        task_api.create(test_project, "任务1", priority="P0")
        task_api.create(test_project, "任务2", priority="P1")

        resp = stats_api.project_stats(test_project)
        data = resp.json()

        assert data["code"] == 200
        assert "data" in data

    def test_project_stats_empty(self, stats_api, test_project):
        """没有任务时的统计"""
        resp = stats_api.project_stats(test_project)
        data = resp.json()

        assert data["code"] == 200

    def test_project_stats_not_found(self, stats_api):
        """项目不存在"""
        resp = stats_api.project_stats(999999)
        data = resp.json()

        assert data["code"] != 200


class TestUserStats:
    """用户统计 GET /api/stats/user/{id}"""

    def test_user_stats_success(self, stats_api):
        """正常获取用户统计"""
        resp = stats_api.user_stats(1)  # admin用户
        data = resp.json()

        assert data["code"] == 200
        assert "data" in data
