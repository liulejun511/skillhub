"""循环成本/步数预算：超额优雅停止（设计 H6 / R13.2）。"""
from __future__ import annotations


class Budget:
    """简单步数/成本预算。total=None 表示无限制。"""

    def __init__(self, total=None):
        self.total = total
        self._spent = 0

    def spend(self, n: int = 1) -> None:
        self._spent += n

    def spent(self) -> int:
        return self._spent

    def remaining(self):
        return float("inf") if self.total is None else max(0, self.total - self._spent)

    def over(self) -> bool:
        return self.total is not None and self._spent >= self.total
