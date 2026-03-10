from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .baseline import run_plain_single_agent_and_save
from .nghe import CustomerRequirement, find_cr, load_nghe_customer_requirements
from .runners import run_one_level_and_save
from .workflow import DecompositionInputs


def compare_two_methods_one_level_and_save(
    *,
    inputs: DecompositionInputs,
    available_modules: List[str],
    known_interfaces: List[str],
    outdir: str | Path,
    run_id: Optional[str] = None,
    model_ours: Optional[str] = None,
    model_baseline: Optional[str] = None,
    workflow_prefix: str = "workflow",
    baseline_prefix: str = "baseline",
) -> Dict[str, Any]:
    ours = run_one_level_and_save(
        inputs=inputs,
        available_modules=available_modules,
        known_interfaces=known_interfaces,
        outdir=outdir,
        filename_prefix=workflow_prefix,
        run_id=run_id,
        model=model_ours,
    )

    baseline = run_plain_single_agent_and_save(
        inputs=inputs,
        available_modules=available_modules,
        known_interfaces=known_interfaces,
        outdir=outdir,
        run_id=run_id,
        model=model_baseline,
        filename_prefix=baseline_prefix,
    )

    return {
        "run_id": run_id,
        "ours": ours,
        "baseline": baseline,
    }


def compare_nghe_cr_and_save(
    *,
    requirements_file: str | Path,
    cr_id: str,
    outdir: str | Path,
    available_modules: List[str],
    known_interfaces: List[str],
    model_ours: Optional[str] = None,
    model_baseline: Optional[str] = None,
    run_id: Optional[str] = None,
    workflow_prefix: str = "workflow",
    baseline_prefix: str = "baseline",
) -> Dict[str, Any]:
    reqs = load_nghe_customer_requirements(requirements_file)
    cr: CustomerRequirement = find_cr(reqs, cr_id)

    mission_system = "Next Generation Heavy Equipment (NGHE) solution for productivity, effectiveness, and safety."
    stakeholders = [
        "Site Manager",
        "Equipment Operator",
        "Tele-operator",
        "Safety Manager",
        "Maintenance/Quality",
        "System Engineer",
        "Project Manager",
    ]

    constraints = [
        f"Acceptance criteria: {cr.acceptance_criteria}",
        "Worksite safety plan and operational policies",
    ]

    candidate_fr = f"{cr.req_id} ({cr.title}): {cr.statement}"

    inputs = DecompositionInputs(
        mission_system=mission_system,
        stakeholders=stakeholders,
        constraints=constraints,
        candidate_fr=candidate_fr,
        risk_tailoring_factors=["Safety criticality: high"],
    )

    return compare_two_methods_one_level_and_save(
        inputs=inputs,
        available_modules=available_modules,
        known_interfaces=known_interfaces,
        outdir=outdir,
        run_id=run_id or cr.req_id,
        model_ours=model_ours,
        model_baseline=model_baseline,
        workflow_prefix=workflow_prefix,
        baseline_prefix=baseline_prefix,
    )
