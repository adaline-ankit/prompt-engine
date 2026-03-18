from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from prompt_engine.engine.optimizer import PromptOptimizationEngine
from prompt_engine.evals.scoring import score_case


DEFAULT_EVAL_PATH = Path("evals/test_cases.json")


def run_evaluations(path: str | Path = DEFAULT_EVAL_PATH) -> dict[str, Any]:
    cases = json.loads(Path(path).read_text())
    engine = PromptOptimizationEngine()
    results = []

    for case in cases:
        runs = [
            engine.optimize_prompt(case["prompt"], context=case.get("context", {}))
            for _ in range(case.get("repeat_runs", 3))
        ]
        results.append(score_case(case, runs))

    summary = {
        "cases": len(results),
        "passed": sum(1 for result in results if result["pass"]),
        "failed": sum(1 for result in results if not result["pass"]),
        "average_overall": round(mean(result["overall"] for result in results), 3) if results else 0.0,
        "results": results,
    }
    return summary


def main() -> int:
    summary = run_evaluations()
    print(json.dumps(summary, indent=2))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

