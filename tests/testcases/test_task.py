"""任务管理接口测试用例"""
import pytest
import allure
from tests.api.task_api import TaskApi
from tests.api.project_api import ProjectApi


@allure.epic("任务模块")
@allure.feature("创建任务")
class TestCreateTask:
    """创建任务 POST /api/tasks"""

    def test_create_task_required_fields(self, task_api, test_project):
        """只填必填参数"""
        resp = task_api.create(test_project, "写单元测试")
        data = resp.json()

        assert data["code"] == 200
        assert "task_id" in data["data"]
        assert data["data"]["title"] == "写单元测试"

    def test_create_task_all_fields(self, task_api, test_project):
        """全部参数"""
        resp = task_api.create(
            test_project, "修复登录bug",
            priority="P0", description="线上用户反馈登录超时"
        )
        data = resp.json()

        assert data["code"] == 200

    def test_create_task_without_title(self, task_api, test_project):
        """缺少title"""
        resp = task_api.post("/api/tasks", {"project_id": test_project})

        assert resp.status_code != 200

    def test_create_task_empty_title(self, task_api, test_project):
        """title为空字符串"""
        resp = task_api.create(test_project, "")

        assert resp.status_code != 200

    def test_create_task_invalid_priority(self, task_api, test_project):
        """priority非法值"""
        resp = task_api.post("/api/tasks", {
            "project_id": test_project, "title": "测试", "priority": "P5"
        })

        assert resp.status_code != 200

    def test_create_task_as_non_member(self, member_api, test_project):
        """非项目成员创建任务"""
        task = TaskApi()
        task.session = member_api.session
        resp = task.create(test_project, "越权创建")
        data = resp.json()

        assert data["code"] == 403

    def test_create_task_verify_in_list(self, task_api, test_project):
        """创建后查列表确认写入"""
        create_resp = task_api.create(test_project, "验证写入")
        task_id = create_resp.json()["data"]["task_id"]

        list_resp = task_api.list(test_project)
        items = list_resp.json()["data"]["items"]
        task_ids = [t["id"] for t in items]

        assert task_id in task_ids


@allure.epic("任务模块")
@allure.feature("任务列表")
class TestListTasks:
    """任务列表 GET /api/tasks"""

    def test_list_tasks_success(self, task_api, test_project, test_task):
        """正常查询"""
        resp = task_api.list(test_project)
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["total"] >= 1

    def test_list_tasks_filter_by_status(self, task_api, test_project, test_task):
        """按状态筛选"""
        resp = task_api.list(test_project, status="todo")
        data = resp.json()

        assert data["code"] == 200
        for item in data["data"]["items"]:
            assert item["status"] == "todo"

    def test_list_tasks_filter_by_priority(self, task_api, test_project, test_task):
        """按优先级筛选"""
        resp = task_api.list(test_project, priority="P2")
        data = resp.json()

        assert data["code"] == 200
        for item in data["data"]["items"]:
            assert item["priority"] == "P2"

    def test_list_tasks_pagination(self, task_api, test_project, test_task):
        """分页"""
        resp = task_api.list(test_project, page=1, page_size=1)
        data = resp.json()

        assert data["code"] == 200
        assert len(data["data"]["items"]) <= 1

    def test_list_tasks_non_member(self, member_api, test_project, test_task):
        """非成员查任务列表"""
        task = TaskApi()
        task.session = member_api.session
        resp = task.list(test_project)
        data = resp.json()

        assert data["code"] == 403


@allure.epic("任务模块")
@allure.feature("任务详情")
class TestGetTaskDetail:
    """任务详情 GET /api/tasks/{id}"""

    def test_get_task_detail(self, task_api, test_task):
        """正常获取"""
        resp = task_api.get_detail(test_task)
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["id"] == test_task
        assert "comments" in data["data"]

    def test_get_task_not_found(self, task_api):
        """任务不存在"""
        resp = task_api.get_detail(999999)
        data = resp.json()

        assert data["code"] != 200
        assert "不存在" in data["msg"]


@allure.epic("任务模块")
@allure.feature("更新任务")
class TestUpdateTask:
    """更新任务 PUT /api/tasks/{id}"""

    def test_update_task_title(self, task_api, test_task):
        """修改标题"""
        resp = task_api.update(test_task, title="改了标题")
        data = resp.json()

        assert data["code"] == 200

        detail = task_api.get_detail(test_task).json()
        assert detail["data"]["title"] == "改了标题"

    def test_update_task_priority(self, task_api, test_task):
        """修改优先级"""
        resp = task_api.update(test_task, priority="P0")
        data = resp.json()

        assert data["code"] == 200

    def test_update_task_not_found(self, task_api):
        """更新不存在的任务"""
        resp = task_api.update(999999, title="不存在")
        data = resp.json()

        assert data["code"] != 200


@allure.epic("任务模块")
@allure.feature("任务状态流转")
class TestUpdateTaskStatus:
    """任务状态流转 PUT /api/tasks/{id}/status"""

    def test_todo_to_in_progress(self, task_api, test_task):
        """正常流转：todo → in_progress"""
        resp = task_api.update_status(test_task, "in_progress")
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["status"] == "in_progress"

    def test_in_progress_to_done(self, task_api, test_task):
        """正常流转：in_progress → done"""
        task_api.update_status(test_task, "in_progress")
        resp = task_api.update_status(test_task, "done")
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["status"] == "done"

    def test_todo_to_done_invalid(self, task_api, test_task):
        """非法流转：todo → done"""
        resp = task_api.update_status(test_task, "done")
        data = resp.json()

        assert data["code"] != 200
        assert "不允许" in data["msg"]

    def test_todo_to_archived_invalid(self, task_api, test_task):
        """非法流转：todo → archived"""
        resp = task_api.update_status(test_task, "archived")
        data = resp.json()

        assert data["code"] != 200
        assert "不允许" in data["msg"]

    def test_done_to_archived(self, task_api, test_task):
        """正常流转：todo → in_progress → done → archived"""
        task_api.update_status(test_task, "in_progress")
        task_api.update_status(test_task, "done")
        resp = task_api.update_status(test_task, "archived")
        data = resp.json()

        assert data["code"] == 200
        assert data["data"]["status"] == "archived"

    def test_status_transition_not_found(self, task_api):
        """不存在的任务"""
        resp = task_api.update_status(999999, "in_progress")
        data = resp.json()

        assert data["code"] != 200


@allure.epic("任务模块")
@allure.feature("删除任务")
class TestDeleteTask:
    """删除任务 DELETE /api/tasks/{id}"""

    def test_delete_task_success(self, task_api, test_project):
        """创建者删除任务"""
        create_resp = task_api.create(test_project, "要删除的任务")
        task_id = create_resp.json()["data"]["task_id"]

        resp = task_api.delete_task(task_id)
        data = resp.json()

        assert data["code"] == 200

    def test_delete_task_not_found(self, task_api):
        """删除不存在的任务"""
        resp = task_api.delete_task(999999)
        data = resp.json()

        assert data["code"] != 200


@allure.epic("任务模块")
@allure.feature("任务评论")
class TestTaskComments:
    """任务评论"""

    def test_add_comment(self, task_api, test_task):
        """添加评论"""
        resp = task_api.add_comment(test_task, "这个任务需要加个缓存")
        data = resp.json()

        assert data["code"] == 200
        assert "comment_id" in data["data"]

    def test_list_comments(self, task_api, test_task):
        """获取评论列表"""
        task_api.add_comment(test_task, "第一条评论")
        task_api.add_comment(test_task, "第二条评论")

        resp = task_api.list_comments(test_task)
        data = resp.json()

        assert data["code"] == 200
        assert len(data["data"]) >= 2

    def test_add_comment_task_not_found(self, task_api):
        """给不存在的任务加评论"""
        resp = task_api.add_comment(999999, "评论")
        data = resp.json()

        assert data["code"] != 200
