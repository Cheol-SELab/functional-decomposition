from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _score_to_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, str) and v.strip().upper() == "N/A":
        return None
    return None


def _sum_side(scores: Dict[str, Any], side: str) -> int:
    total = 0
    for item in scores.values():
        if not isinstance(item, dict):
            continue
        n = _score_to_int(item.get(side))
        if n is not None:
            total += n
    return total


def _extract_cr_id(run_id: Optional[str]) -> Optional[str]:
    if not run_id:
        return None
    # Common patterns we used:
    # - CR-NGHE-008_trial3
    # - CR-NGHE-008_containment_retry_trial2
    # - CR-NGHE-008
    if run_id.startswith("CR-"):
        return run_id.split("_")[0]
    return None


def _flatten_evaluation(path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "evaluation_file": str(path),
        "run_id": data.get("run_id"),
    }

    out["cr_id"] = _extract_cr_id(out.get("run_id"))

    inputs = data.get("inputs") if isinstance(data.get("inputs"), dict) else {}
    out["ours_file"] = inputs.get("ours_file")
    out["baseline_file"] = inputs.get("baseline_file")

    evaluation = data.get("evaluation") if isinstance(data.get("evaluation"), dict) else {}
    summary = evaluation.get("summary") if isinstance(evaluation.get("summary"), dict) else {}

    out["winner"] = summary.get("winner")
    out["why"] = summary.get("why")

    scores = evaluation.get("scores") if isinstance(evaluation.get("scores"), dict) else {}

    # Totals: prefer explicit totals if present, else compute.
    ours_total = summary.get("ours_total_score")
    baseline_total = summary.get("baseline_total_score")

    if not isinstance(ours_total, int):
        ours_total = _sum_side(scores, "ours")
    if not isinstance(baseline_total, int):
        baseline_total = _sum_side(scores, "baseline")

    out["ours_total_score"] = ours_total
    out["baseline_total_score"] = baseline_total
    out["delta_ours_minus_baseline"] = ours_total - baseline_total

    # Flatten per-category scores.
    for cat, item in scores.items():
        if not isinstance(item, dict):
            continue
        out[f"{cat}_ours"] = _score_to_int(item.get("ours"))
        out[f"{cat}_baseline"] = _score_to_int(item.get("baseline"))

    return out


def _write_csv(csv_path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    fieldnames: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def _aggregate_by_cr(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Simple aggregation for paper tables: counts + average totals.
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        cr_id = r.get("cr_id")
        if not isinstance(cr_id, str) or not cr_id:
            continue
        grouped.setdefault(cr_id, []).append(r)

    out: List[Dict[str, Any]] = []
    for cr_id, rs in sorted(grouped.items()):
        ours_totals = [r.get("ours_total_score") for r in rs if isinstance(r.get("ours_total_score"), int)]
        base_totals = [r.get("baseline_total_score") for r in rs if isinstance(r.get("baseline_total_score"), int)]
        deltas = [
            (r.get("ours_total_score") - r.get("baseline_total_score"))
            for r in rs
            if isinstance(r.get("ours_total_score"), int) and isinstance(r.get("baseline_total_score"), int)
        ]
        winners = [r.get("winner") for r in rs]

        # Paired sign test (non-parametric) on deltas; exact two-sided p-value under H0 p=0.5
        non_tie_deltas = [d for d in deltas if isinstance(d, int) and d != 0]
        n_non_ties = len(non_tie_deltas)
        k_pos = sum(1 for d in non_tie_deltas if d > 0)

        sign_p_value: Optional[float]
        if n_non_ties == 0:
            sign_p_value = None
        else:
            # X ~ Bin(n_non_ties, 0.5)
            def cdf(k: int) -> float:
                return sum(math.comb(n_non_ties, i) for i in range(0, k + 1)) / (2**n_non_ties)

            p_le = cdf(k_pos)
            p_ge = 1.0 - cdf(k_pos - 1) if k_pos > 0 else 1.0
            sign_p_value = min(1.0, 2.0 * min(p_le, p_ge))

        def std_or_none(xs: List[int]) -> Optional[float]:
            if len(xs) < 2:
                return None
            return statistics.stdev(xs)

        out.append(
            {
                "cr_id": cr_id,
                "n": len(rs),
                "ours_win": sum(1 for w in winners if w == "OURS"),
                "baseline_win": sum(1 for w in winners if w == "BASELINE"),
                "tie": sum(1 for w in winners if w == "TIE"),
                "ours_avg_total": (sum(ours_totals) / len(ours_totals)) if ours_totals else None,
                "baseline_avg_total": (sum(base_totals) / len(base_totals)) if base_totals else None,
                "avg_delta": ((sum(ours_totals) / len(ours_totals)) - (sum(base_totals) / len(base_totals)))
                if (ours_totals and base_totals)
                else None,
                "ours_std_total": std_or_none(ours_totals),
                "baseline_std_total": std_or_none(base_totals),
                "delta_std": std_or_none(deltas),
                "n_non_ties": n_non_ties,
                "sign_test_p_value": sign_p_value,
            }
        )

    return out


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser(description="Export output/evaluation_*.json into a CSV summary for paper tables.")
    p.add_argument("--output-dir", default="output")
    p.add_argument("--glob", default="evaluation_*.json")
    p.add_argument("--csv", default="output/evaluation_summary.csv")
    p.add_argument("--csv-by-cr", default="output/evaluation_summary_by_cr.csv")
    args = p.parse_args()

    outdir = Path(args.output_dir)
    paths = sorted(outdir.glob(args.glob))

    rows: List[Dict[str, Any]] = []
    for path in paths:
        try:
            data = _load_json(path)
            rows.append(_flatten_evaluation(path, data))
        except Exception as e:
            # Keep going: a single corrupt file shouldn't block export.
            rows.append({"evaluation_file": str(path), "error": str(e)})

    csv_path = Path(args.csv)
    _write_csv(csv_path, rows)

    by_cr = _aggregate_by_cr([r for r in rows if "error" not in r])
    by_cr_path = Path(args.csv_by_cr)
    _write_csv(by_cr_path, by_cr)

    print(str(csv_path))
    print(str(by_cr_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
