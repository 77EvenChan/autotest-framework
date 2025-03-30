from tests.api.base_api import BaseApi


class TaskApi(BaseApi):
    """任务管理接口封装"""

    def create(self, project_id: int, title: str, priority: str = "P2",
               assignee_id: int = None, description: str = ""):
        data = {
            "project_id": project_id, "title": title,
            "priority": priority, "description": description
        }
        if assignee_id:
            data["assignee_id"] = assignee_id
        return self.post("/api/tasks", data)

    def list(self, project_id: int, status: str = None, priority: str = None,
             assignee_id: int = None, page: int = 1, page_size: int = 20):
        params = {"project_id": project_id, "page": page, "page_size": page_size}
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        if assignee_id:
            params["assignee_id"] = assignee_id
        return self.get("/api/tasks", params=params)

    def get_detail(self, task_id: int):
        return self.get(f"/api/tasks/{task_id}")

    def update(self, task_id: int, **kwargs):
        return self.put(f"/api/tasks/{task_id}", kwargs)

    def update_status(self, task_id: int, status: str):
        return self.put(f"/api/tasks/{task_id}/status", {"status": status})

    def delete(self, task_id: int):
        return self.delete(f"/api/tasks/{task_id}")

    def add_comment(self, task_id: int, content: str):
        return self.post(f"/api/tasks/{task_id}/comments", {"content": content})

    def list_comments(self, task_id: int):
        return self.get(f"/api/tasks/{task_id}/comments")