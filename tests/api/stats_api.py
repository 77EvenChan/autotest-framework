from tests.api.base_api import BaseApi


class StatsApi(BaseApi):
    """数据统计接口封装"""

    def project_stats(self, project_id: int):
        return self.get(f"/api/stats/project/{project_id}")

    def user_stats(self, user_id: int):
        return self.get(f"/api/stats/user/{user_id}")