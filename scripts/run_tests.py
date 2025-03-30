"""测试运行脚本 — 支持多种运行模式

用法：
    python scripts/run_tests.py              # 运行全部测试
    python scripts/run_tests.py --smoke      # 只跑冒烟测试
    python scripts/run_tests.py --report     # 运行并生成 Allure 报告
    python scripts/run_tests.py --module auth  # 只跑认证模块
"""
import subprocess
import sys
import os
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent.parent
os.chdir(ROOT)


def run_tests(args=None, report=False):
    """运行 pytest 测试"""
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v"]

    if args:
        cmd.extend(args)

    if report:
        cmd.extend(["--alluredir=reports/allure-results", "--clean-alluredir"])

    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if report and result.returncode is not None:
        print("\n" + "=" * 50)
        print("Allure 报告数据已生成到 reports/allure-results/")
        print("查看报告：")
        print("  allure serve reports/allure-results")
        print("  或者：")
        print("  allure generate reports/allure-results -o reports/allure-report --clean")
        print("  然后打开 reports/allure-report/index.html")
        print("=" * 50)

    return result.returncode


def main():
    args = sys.argv[1:]
    report = "--report" in args
    if report:
        args.remove("--report")

    # 模块过滤
    module_map = {
        "auth": "tests/testcases/test_auth.py",
        "project": "tests/testcases/test_project.py",
        "task": "tests/testcases/test_task.py",
        "stats": "tests/testcases/test_stats.py",
        "data": "tests/testcases/test_data_driven.py",
    }

    if "--module" in args:
        idx = args.index("--module")
        if idx + 1 < len(args):
            module = args[idx + 1]
            if module in module_map:
                args = [module_map[module]] + args[:idx] + args[idx + 2:]
            else:
                print(f"未知模块: {module}")
                print(f"可用模块: {', '.join(module_map.keys())}")
                sys.exit(1)

    # 冒烟测试标记
    if "--smoke" in args:
        args.remove("--smoke")
        args.extend(["-m", "smoke"])

    exit_code = run_tests(args, report)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
