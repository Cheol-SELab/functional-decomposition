from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .env import load_default_env
from .llm import OpenAIResponsesClient
from .output import save_run_json
from .workflow import DecompositionInputs


def run_plain_single_agent(
    *,
    inputs: DecompositionInputs,
    available_modules: List[str],
    known_interfaces: List[str],
    model: Optional[str] = None,
) -> Dict[str, Any]:
    system = "ROLE: Systems engineering assistant."

    user = (
        "TASK: Perform one full functional decomposition level using a single-pass approach. "
        "You must produce the same artifacts as a multi-step FR->DP->IM workflow (FR refinement, DP selection, IM assignment, gate review, and a stop/zigzag decision) "
        "but do it in one response.\n\n"
        "CONTEXT:\n"
        f"- Mission/System: {inputs.mission_system}\n"
        f"- Stakeholders: {', '.join(inputs.stakeholders) if inputs.stakeholders else '<none>'}\n"
        f"- Constraints: {', '.join(inputs.constraints) if inputs.constraints else '<none>'}\n"
        f"- Available modules (IM candidates): {', '.join(available_modules) if available_modules else '<unknown>'}\n"
        f"- Known interfaces: {', '.join(known_interfaces) if known_interfaces else '<unknown>'}\n\n"
        "INPUT:\n"
        f"- Candidate FR: {inputs.candidate_fr}\n"
        f"- Risk tailoring factors: {', '.join(inputs.risk_tailoring_factors) if inputs.risk_tailoring_factors else '<none>'}\n\n"
        "OUTPUT FORMAT (JSON ONLY):\n"
        "{\n"
        '  "refined_fr": {"refined_fr": "...", "rationale": "...", "verification_idea": "...", "sub_frs": ["..."], "is_atomic": true},\n'
        '  "selected_dp": {"candidate_dps": ["..."], "selected_dp": "...", "coupling_check": {"assessment": "Pass|Fail", "potential_sources": ["..."], "notes": "..."}, "assumptions_risks": ["..."], "recommended_revision": "..."},\n'
        '  "assigned_im": {"im_boundary": {"name": "...", "scope": "..."}, "external_interfaces": [{"name": "...", "direction": "in|out|inout", "details": "..."}], "ownership_candidate": "...", "containment_hypothesis": "..."},\n'
        '  "gate_review": {"fr_dp_gate": {"pass": true, "reason": "..."}, "dp_im_gate": {"pass": true, "diffusion_risks": ["..."]}, "fr_im_gate": {"pass": true, "verification_feasibility": "...", "allocation_clarity": "..."}, "recommended_revisions": ["..."]},\n'
        '  "decision": {"decision": "STOP|ZIGZAG_DOWN|REVISE_CURRENT_LEVEL", "justification": "...", "next_level_sub_frs": ["..."], "revise": {"target": "FR|DP|IM|", "why": "..."}, "record": {"assumptions": ["..."], "open_risks": ["..."], "evidence_needed": ["..."]}}\n'
        "}\n"
    )

    load_default_env()
    client = OpenAIResponsesClient()
    return client.complete_json(system=system, user=user, schema_hint=None, model=model)


def run_plain_single_agent_and_save(
    *,
    inputs: DecompositionInputs,
    available_modules: List[str],
    known_interfaces: List[str],
    outdir: str | Path,
    run_id: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    payload = run_plain_single_agent(
        inputs=inputs,
        available_modules=available_modules,
        known_interfaces=known_interfaces,
        model=model,
    )

    file_path = save_run_json(payload=payload, outdir=outdir, filename_prefix="baseline", run_id=run_id)
    payload["_output_file"] = str(file_path)
    return payload
