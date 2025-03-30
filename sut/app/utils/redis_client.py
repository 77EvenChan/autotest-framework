import redis
from app.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

pool = redis.ConnectionPool(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD,
    db=REDIS_DB, decode_responses=True
)
redis_client = redis.Redis(connection_pool=pool)
