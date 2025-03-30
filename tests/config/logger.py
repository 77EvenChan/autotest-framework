import logging
from pathlib import Path
from tests.config.config_loader import load_config


def setup_logger(name: str = "taskflow_test") -> logging.Logger:
    """创建测试日志记录器，全局复用"""
    logger = logging.getLogger(name)

    # 防止重复添加 handler（Python logger 是全局单例）
    if logger.handlers:
        return logger

    # 从配置文件读日志级别
    cfg = load_config()
    level = getattr(logging, cfg.get("logging", {}).get("level", "INFO"))
    logger.setLevel(level)

    # Handler 1：控制台输出（开发时看）
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"  # 只显示 时:分:秒
    ))
    logger.addHandler(console)

    # Handler 2：文件输出（事后排查用）
    log_file = cfg.get("logging", {}).get("log_file", "reports/test.log")
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)  # 自动创建目录
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    ))
    logger.addHandler(file_handler)

    return logger