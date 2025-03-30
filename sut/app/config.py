import os

# 数据库配置
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "taskflow")
DB_PASSWORD = os.getenv("DB_PASSWORD", "taskflow123")
DB_NAME = os.getenv("DB_NAME", "taskflow")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Redis配置
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redis123")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "taskflow-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 登录失败锁定
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCK_SECONDS = 1800  # 30分钟

# 限流配置
RATE_LIMIT_PER_MINUTE = 60
