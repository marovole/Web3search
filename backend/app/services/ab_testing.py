from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ABTestResult:
    name: str
    variant_a: float
    variant_b: float
    winner: str

    def to_dict(self) -> Dict[str, float | str]:
        return {
            "name": self.name,
            "variant_a": self.variant_a,
            "variant_b": self.variant_b,
            "winner": self.winner,
        }


class ABTestManager:
    def __init__(self) -> None:
        self._results: Dict[str, ABTestResult] = {
            "cta-color": ABTestResult("cta-color", 0.12, 0.15, "variant_b"),
        }

    def list_tests(self) -> List[str]:
        return list(self._results.keys())

    def get_result(self, test_name: str) -> Optional[ABTestResult]:
        return self._results.get(test_name)


ab_test_manager = ABTestManager()
