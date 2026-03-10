from __future__ import annotations

import argparse
from pathlib import Path

from lfd.experiment_suite import (
    CrossEvalExperimentSuiteConfig,
    ExperimentSuiteConfig,
    run_nghe_cross_eval_experiment_suite_to_csv,
    run_nghe_experiment_suite_to_csv,
)


def _split_csv_arg(v: str) -> list[str]:
    parts = [p.strip() for p in v.split(",")]
    return [p for p in parts if p]


def main() -> int:
    p = argparse.ArgumentParser(description="Run NGHE experiment suite and export a consolidated CSV.")

    p.add_argument("--requirements-file", default="example/NGHE_customer_requirements.md")
    p.add_argument("--outdir", default="output")
    p.add_argument("--csv", default="output/experiment_results.csv")

    p.add_argument(
        "--cr-ids",
        default="CR-NGHE-008,CR-NGHE-012,CR-NGHE-014,CR-NGHE-020",
        help="Comma-separated CR IDs.",
    )
    p.add_argument("--trials", type=int, default=3)

    p.add_argument(
        "--available-modules",
        default="NGHE Solution,Vehicle,Teleoperation,Safety Services",
        help="Comma-separated module names.",
    )
    p.add_argument(
        "--known-interfaces",
        default="Telemetry,Tasking,SafetyAlert,Network Link",
        help="Comma-separated interface names.",
    )

    p.add_argument("--model-ours", default=None)
    p.add_argument("--model-baseline", default=None)
    p.add_argument("--model-eval", default=None)

    p.add_argument(
        "--models",
        default=None,
        help="Comma-separated model names for cross-evaluation mode. "
             "Each model produces outputs, and every OTHER model evaluates them. "
             "E.g. gpt-4.1-mini,claude-haiku-4-5,gemini-3-flash-preview",
    )

    args = p.parse_args()

    if args.models:
        producer_models = _split_csv_arg(args.models)
        config = CrossEvalExperimentSuiteConfig(
            requirements_file=args.requirements_file,
            outdir=args.outdir,
            cr_ids=_split_csv_arg(args.cr_ids),
            trials_per_cr=args.trials,
            available_modules=_split_csv_arg(args.available_modules),
            known_interfaces=_split_csv_arg(args.known_interfaces),
            producer_models=producer_models,
        )
        out_path = run_nghe_cross_eval_experiment_suite_to_csv(
            config=config,
            csv_path=Path(args.csv),
        )
    else:
        config = ExperimentSuiteConfig(
            requirements_file=args.requirements_file,
            outdir=args.outdir,
            cr_ids=_split_csv_arg(args.cr_ids),
            trials_per_cr=args.trials,
            available_modules=_split_csv_arg(args.available_modules),
            known_interfaces=_split_csv_arg(args.known_interfaces),
            model_ours=args.model_ours,
            model_baseline=args.model_baseline,
            model_eval=args.model_eval,
        )
        out_path = run_nghe_experiment_suite_to_csv(
            config=config,
            csv_path=Path(args.csv),
        )

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
