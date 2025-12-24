from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .evaluator import evaluate_two_output_files_and_save
from .experiment import compare_nghe_cr_and_save


@dataclass(frozen=True)
class ExperimentSuiteConfig:
    requirements_file: str | Path
    outdir: str | Path
    cr_ids: List[str]
    trials_per_cr: int
    available_modules: List[str]
    known_interfaces: List[str]
    model_ours: Optional[str] = None
    model_baseline: Optional[str] = None
    model_eval: Optional[str] = None


def _score_value(v: Any) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().upper() == "N/A":
        return None
    return None


def _flatten_eval_scores(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}

    summary = evaluation.get("summary") if isinstance(evaluation.get("summary"), dict) else {}
    out["winner"] = summary.get("winner")
    out["why"] = summary.get("why")
    out["ours_total_score"] = summary.get("ours_total_score")
    out["baseline_total_score"] = summary.get("baseline_total_score")

    scores = evaluation.get("scores") if isinstance(evaluation.get("scores"), dict) else {}
    for cat, item in scores.items():
        if not isinstance(item, dict):
            continue
        out[f"{cat}_ours"] = _score_value(item.get("ours"))
        out[f"{cat}_baseline"] = _score_value(item.get("baseline"))
    return out


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def run_nghe_experiment_suite_to_csv(
    *,
    config: ExperimentSuiteConfig,
    csv_path: str | Path,
    workflow_variant: str = "ours_workflow",
    baseline_variant: str = "baseline_single_pass",
    skip_existing: bool = True,
) -> Path:
    csv_path = Path(csv_path)
    _ensure_parent_dir(csv_path)

    rows: List[Dict[str, Any]] = []
    outdir = Path(config.outdir)

    for cr_id in config.cr_ids:
        for trial in range(1, config.trials_per_cr + 1):
            run_id = f"{cr_id}_trial{trial}"

            # Check if evaluation file already exists
            if skip_existing:
                existing_eval = list(outdir.glob(f"evaluation_{run_id}_*.json"))
                if existing_eval:
                    print(f"Skipping {run_id} - evaluation file already exists: {existing_eval[0].name}")
                    continue

            print(f"Running experiment: {run_id}")

            comp = compare_nghe_cr_and_save(
                requirements_file=config.requirements_file,
                cr_id=cr_id,
                outdir=config.outdir,
                available_modules=config.available_modules,
                known_interfaces=config.known_interfaces,
                model_ours=config.model_ours,
                model_baseline=config.model_baseline,
            )

            ours_path = comp["ours"].get("_output_file")
            baseline_path = comp["baseline"].get("_output_file")
            if not isinstance(ours_path, str) or not isinstance(baseline_path, str):
                raise RuntimeError("Experiment did not produce expected _output_file paths")

            ev = evaluate_two_output_files_and_save(
                ours_path=ours_path,
                baseline_path=baseline_path,
                outdir=config.outdir,
                run_id=run_id,
                model=config.model_eval,
            )

            evaluation = ev.get("evaluation") if isinstance(ev.get("evaluation"), dict) else {}
            flat_scores = _flatten_eval_scores(evaluation)

            rows.append(
                {
                    "cr_id": cr_id,
                    "trial": trial,
                    "run_id": run_id,
                    "workflow_variant": workflow_variant,
                    "baseline_variant": baseline_variant,
                    "model_ours": config.model_ours,
                    "model_baseline": config.model_baseline,
                    "model_eval": config.model_eval,
                    "available_modules": "|".join(config.available_modules),
                    "known_interfaces": "|".join(config.known_interfaces),
                    "ours_output_file": ours_path,
                    "baseline_output_file": baseline_path,
                    "evaluation_output_file": ev.get("_output_file"),
                    **flat_scores,
                }
            )

    if not rows:
        print("No new experiments to run - all trials already exist")
    else:
        _write_csv(csv_path, rows)
        print(f"Wrote {len(rows)} new experiment results to {csv_path}")
    
    return csv_path


def _write_csv(csv_path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    fieldnames: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
