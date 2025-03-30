import time
import logging
from fastapi import Request

logger = logging.getLogger("taskflow")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
logger.addHandler(handler)


async def request_logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    cost = round((time.time() - start) * 1000, 2)
    logger.info(
        "%s %s %d %sms",
        request.method, request.url.path, response.status_code, cost
    )
    return response
