"""项目管理接口测试用例"""
import pytest
from tests.api.project_api import ProjectApi


class TestCreateProject:
    """创建项目 POST /api/projects"""

    def test_create_project_success(self, project_api):
        """正常创建项目"""
        import time
        name = f"新项目_{int(time.time())}"
        resp = project_api.create(name, "这是描述")
        data = resp.json()

        assert data["code"] == 200
        assert "project_id" in data["data"]
        assert data["data"]["name"] == name

    def test_create_project_without_description(self, project_api):
        """不传描述，只传名称"""
        import time
        resp = project_api.create(f"无描述_{int(time.time())}")
        data = resp.json()

        assert data["code"] == 200

    def test_create_project_duplicate_name(self, project_api, test_project):
        """同名项目重复创建"""
        # 先获取test_project的真实名称
        detail = project_api.get_detail(test_project).json()
        existing_name = detail["data"]["name"]
        resp = project_api.create(existing_name)
        data = resp.json()

        assert data["code"] != 200
        assert "同名" in data["msg"]

    def test_create_project_empty_name(self, project_api):
        """项目名称为空"""
        resp = project_api.post("/api/projects", {"name": "", "description": "空名称"})

        assert resp.status_code != 200


class TestListProjects:
    """项目列表 GET /api/projects"""

    def test_list_projects_success(self, project_api, test_project):
        """正常查询项目列表"""
        resp = project_api.list()
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["total"] >= 1
        assert len(data["data"]["items"]) >= 1

    def test_list_projects_pagination(self, project_api, test_project):
        """分页查询"""
        resp = project_api.list(page=1, page_size=1)
        data = resp.json()

        assert data["code"] == 200
        assert len(data["data"]["items"]) <= 1

    def test_list_projects_empty(self, member_api):
        """普通成员没有项目时列表为空"""
        api = ProjectApi()
        api.session = member_api.session
        resp = api.list()
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["total"] == 0


class TestGetProjectDetail:
    """项目详情 GET /api/projects/{id}"""

    def test_get_project_detail(self, project_api, test_project):
        """正常获取项目详情"""
        resp = project_api.get_detail(test_project)
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["id"] == test_project
        assert "members" in data["data"]

    def test_get_project_not_found(self, project_api):
        """项目不存在"""
        resp = project_api.get_detail(999999)
        data = resp.json()

        assert data["code"] != 200

    def test_get_project_non_member(self, member_api, test_project):
        """非成员访问项目"""
        api = ProjectApi()
        api.session = member_api.session
        resp = api.get_detail(test_project)
        data = resp.json()

        assert data["code"] == 403


class TestUpdateProject:
    """更新项目 PUT /api/projects/{id}"""

    def test_update_project_name(self, project_api, test_project):
        """修改项目名称"""
        resp = project_api.update(test_project, name="改名后的项目")
        data = resp.json()

        assert data["code"] == 200

        # 验证修改生效
        detail = project_api.get_detail(test_project).json()
        assert detail["data"]["name"] == "改名后的项目"

    def test_update_project_by_non_admin(self, member_api, test_project):
        """非管理员修改项目（应失败）"""
        api = ProjectApi()
        api.session = member_api.session
        resp = api.update(test_project, name="越权修改")
        data = resp.json()

        assert data["code"] == 403


class TestDeleteProject:
    """删除项目 DELETE /api/projects/{id}"""

    def test_delete_project_by_non_owner(self, member_api, project_api):
        """非创建者删除项目（应失败）"""
        # 先创建一个项目
        import time
        create_resp = project_api.create(f"要被删的_{int(time.time())}")
        project_id = create_resp.json()["data"]["project_id"]

        # 用member去删
        api = ProjectApi()
        api.session = member_api.session
        resp = api.delete_project(project_id)
        data = resp.json()

        assert data["code"] == 403

        # 清理：admin来删
        project_api.delete_project(project_id)


class TestProjectMembers:
    """项目成员管理"""

    def test_add_member_success(self, project_api, test_project, member_api):
        """添加成员"""
        resp = project_api.add_member(test_project, "testmember", role="member")
        data = resp.json()

        assert data["code"] == 200

        # 验证成员已添加
        detail = project_api.get_detail(test_project).json()
        member_names = [m["username"] for m in detail["data"]["members"]]
        assert "testmember" in member_names

    def test_add_member_duplicate(self, project_api, test_project, member_api):
        """重复添加成员"""
        project_api.add_member(test_project, "testmember")
        resp = project_api.add_member(test_project, "testmember")
        data = resp.json()

        assert data["code"] != 200
        assert "已是" in data["msg"]

    def test_add_member_user_not_found(self, project_api, test_project):
        """添加不存在的用户"""
        resp = project_api.add_member(test_project, "ghost_user_xyz")
        data = resp.json()

        assert data["code"] != 200
        assert "不存在" in data["msg"]
