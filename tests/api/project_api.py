from tests.api.base_api import BaseApi


class ProjectApi(BaseApi):
    """项目管理接口封装"""

    def create(self, name: str, description: str = ""):
        return self.post("/api/projects", {"name": name, "description": description})

    def list(self, status: str = None, page: int = 1, page_size: int = 20):
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        return self.get("/api/projects", params=params)

    def get_detail(self, project_id: int):
        return self.get(f"/api/projects/{project_id}")

    def update(self, project_id: int, name: str = None, description: str = None):
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        return self.put(f"/api/projects/{project_id}", data)

    def delete_project(self, project_id: int):
        return self.delete(f"/api/projects/{project_id}")

    def add_member(self, project_id: int, username: str, role: str = "member"):
        return self.post(f"/api/projects/{project_id}/members",
                         {"username": username, "role": role})

    def remove_member(self, project_id: int, user_id: int):
        return self.session.delete(f"{self.base_url}/api/projects/{project_id}/members/{user_id}")