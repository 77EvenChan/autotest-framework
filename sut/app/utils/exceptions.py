from fastapi import Request
from fastapi.responses import JSONResponse


class BizError(Exception):
    """业务异常基类"""
    def __init__(self, code: int = 400, msg: str = "请求错误"):
        self.code = code
        self.msg = msg


class NotFoundError(BizError):
    def __init__(self, msg: str = "资源不存在"):
        super().__init__(code=404, msg=msg)


class AuthError(BizError):
    def __init__(self, msg: str = "登录已过期，请重新登录"):
        super().__init__(code=401, msg=msg)


class ForbiddenError(BizError):
    def __init__(self, msg: str = "没有权限执行此操作"):
        super().__init__(code=403, msg=msg)


class RateLimitError(BizError):
    def __init__(self, msg: str = "请求过于频繁，请稍后再试"):
        super().__init__(code=429, msg=msg)


async def biz_error_handler(request: Request, exc: BizError):
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "msg": exc.msg, "data": None}
    )


async def global_exception_handler(request: Request, exc: Exception):
    # 生产环境应该记录日志，这里简化处理
    return JSONResponse(
        status_code=500,
        content={"code": 500, "msg": "服务器内部错误，请稍后重试", "data": None}
    )
