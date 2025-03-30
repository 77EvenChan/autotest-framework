"""YAML 测试数据加载器 — 支持数据驱动测试"""
import yaml
from pathlib import Path


def load_yaml(file_name: str, key: str = "cases") -> list:
    """从 tests/data/ 目录加载 YAML 测试数据文件

    Args:
        file_name: YAML 文件名（如 "register_cases.yaml"）
        key: 数据键名，默认 "cases"

    Returns:
        list[dict]: 测试用例列表，每个 dict 是一组参数
    """
    data_path = Path(__file__).parent.parent / "data" / file_name
    with open(data_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict) and key in data:
        return data[key]
    return data


def parametrize_from_yaml(file_name: str, key: str = "cases"):
    """从 YAML 文件读取数据，返回 pytest.mark.parametrize 可用的参数

    Args:
        file_name: YAML 文件名
        key: 数据键名，默认 "cases"

    Returns:
        tuple: (argnames, argvalues) 供 parametrize 使用
    """
    data = load_yaml(file_name)
    cases = data[key] if isinstance(data, dict) else data

    if not cases:
        return "", []

    # 从第一条用例提取字段名作为参数名
    argnames = list(cases[0].keys())
    argvalues = [tuple(case[k] for k in argnames) for case in cases]

    return ",".join(argnames), argvalues
