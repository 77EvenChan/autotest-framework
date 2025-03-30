# Dockerfile — 测试执行环境
# 用法：docker build -t autotest . && docker run --network host autotest

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件（利用 Docker 缓存层，依赖不变时不重新安装）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 默认命令：运行测试
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
