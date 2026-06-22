"""无 pytest 依赖的简易测试运行器（离线本地用）。

CI 用 pytest 跑同一批 test_*；本地无 pytest 时用此脚本：
    PYTHONPATH=tools python tools/tests/run_all.py
发现并执行所有 test_*.py 里的 test_* 函数，打印 PASS/FAIL，全过则退出码 0。
"""
import importlib.util
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(module_path: Path):
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    total = passed = 0
    for test_file in sorted(HERE.glob("test_*.py")):
        module = _load(test_file)
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            fn = getattr(module, name)
            if not callable(fn):
                continue
            total += 1
            try:
                fn()
                passed += 1
                print(f"PASS {test_file.name}::{name}")
            except Exception:
                print(f"FAIL {test_file.name}::{name}")
                traceback.print_exc()
    print(f"\n{passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
