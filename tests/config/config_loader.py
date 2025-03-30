import yaml
from pathlib import Path

_config = None  # 缓存，只读一次文件

def load_config() -> dict:
    """加载配置"""
    global _config
    if _config in None:
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            _config = yaml.safe_load(f)
        return _config