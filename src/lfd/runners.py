from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .env import load_default_env
from .llm import OpenAIResponsesClient
from .nghe import CustomerRequirement, find_cr, load_nghe_customer_requirements
from .output import save_run_json
from .workflow import DecompositionInputs, DecompositionRun, DecompositionWorkflow


def run_one_level_and_save(
    *,
    inputs: DecompositionInputs,
    available_modules: List[str],
    known_interfaces: List[str],
    outdir: str | Path,
    filename_prefix: str,
    run_id: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    load_default_env()

    wf = DecompositionWorkflow(llm=OpenAIResponsesClient(), model=model)
    run: DecompositionRun = wf.run_one_level(
        inputs=inputs,
        available_modules=available_modules,
        known_interfaces=known_interfaces,
    )

    payload: Dict[str, Any] = asdict(run)
    out_path = save_run_json(payload=payload, outdir=outdir, filename_prefix=filename_prefix, run_id=run_id)
    payload["_output_file"] = str(out_path)
    return payload


def run_nghe_cr_and_save(
    *,
    requirements_file: str | Path,
    cr_id: str,
    outdir: str | Path,
    available_modules: List[str],
    known_interfaces: List[str],
    model: Optional[str] = None,
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

    return run_one_level_and_save(
        inputs=inputs,
        available_modules=available_modules,
        known_interfaces=known_interfaces,
        outdir=outdir,
        filename_prefix="nghe",
        run_id=cr.req_id,
        model=model,
    )
