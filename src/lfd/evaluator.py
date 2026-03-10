from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .env import load_default_env
from .llm import make_llm_client
from .output import save_run_json
from .prompts import DOMAIN_CONTEXT, EVALUATION_CRITERIA


def _read_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def _score_to_number(v: Any) -> Optional[int]:
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().upper() == "N/A":
        return None
    return None


def _sum_scores(scores: Dict[str, Any], *, side: str) -> int:
    total = 0
    for item in scores.values():
        if not isinstance(item, dict):
            continue
        n = _score_to_number(item.get(side))
        if n is not None:
            total += n
    return total


def _evaluate_category(
    *,
    client: "LLMClient",
    category_key: str,
    category_title: str,
    category_guidance: str,
    ours: Dict[str, Any],
    baseline: Dict[str, Any],
    model: Optional[str],
) -> Dict[str, Any]:
    system = "ROLE: Systems engineering evaluator.\n\n" + DOMAIN_CONTEXT + "\n" + EVALUATION_CRITERIA

    ours_canon = json.dumps(ours, ensure_ascii=False, sort_keys=True)
    baseline_canon = json.dumps(baseline, ensure_ascii=False, sort_keys=True)
    seed = (category_key + "\n" + ours_canon + "\n" + baseline_canon).encode("utf-8")
    swap = (hashlib.sha256(seed).digest()[0] % 2) == 1
    if swap:
        first_json = baseline_canon
        second_json = ours_canon
    else:
        first_json = ours_canon
        second_json = baseline_canon

    user = (
        "TASK: Evaluate ONE category of functional decomposition quality by comparing Output A vs Output B.\n\n"
        "IMPORTANT:\n"
        "- Evaluate ONLY the requested category.\n"
        "- Use the evaluation criteria provided in the system context.\n"
        "- Score 1-5, or N/A if not applicable / not evidenced.\n"
        "- Keep evidence CONCISE (2-3 sentences max).\n\n"
        f"CATEGORY: {category_title}\n"
        f"GUIDANCE: {category_guidance}\n\n"
        "OUTPUT FORMAT (JSON ONLY):\n"
        "{\n"
        f'  "category": "{category_key}",\n'
        '  "output_a": 0,\n'
        '  "output_b": 0,\n'
        '  "evidence": "brief justification"\n'
        "}\n\n"
        "INPUTS:\n"
        f"Output A JSON: {first_json}\n\n"
        f"Output B JSON: {second_json}\n"
    )

    raw = client.complete_json(system=system, user=user, schema_hint=None, model=model, max_output_tokens=8192)

    if swap:
        return {
            "category": raw.get("category", category_key),
            "ours": raw.get("output_b"),
            "baseline": raw.get("output_a"),
            "evidence": raw.get("evidence", ""),
        }
    else:
        return {
            "category": raw.get("category", category_key),
            "ours": raw.get("output_a"),
            "baseline": raw.get("output_b"),
            "evidence": raw.get("evidence", ""),
        }


def evaluate_two_outputs(
    *,
    ours: Dict[str, Any],
    baseline: Dict[str, Any],
    model: Optional[str] = None,
) -> Dict[str, Any]:
    load_default_env()
    client = make_llm_client(model)

    category_specs = [
        (
            "pure_fr",
            "Pure FR",
            "Problem-vs-solution linguistic checks; atomic single obligation; stop when further decomposition forces technology/algorithm/implementation wording; ensure testability idea exists.",
        ),
        (
            "fr_dp_bridge",
            "FR<->DP Bridge",
            "Independence Axiom / coupling awareness; Information Axiom / avoid unnecessary complexity; risk tailoring; what-vs-how boundary tests.",
        ),
        (
            "dp_im_bridge",
            "DP<->IM Bridge",
            "Module Diffusion / containment of DP within IM boundary; identify diffusion/scattering risks across modules.",
        ),
        (
            "pure_im",
            "Pure IM",
            "Structural evidence such as modularity optimization (Q-score), centrality/stability, DSM clustering. If no structure/graph evidence is present, score N/A.",
        ),
        (
            "fr_im_bridge",
            "FR<->IM Bridge",
            "Verifiability/testability boundary; allocation boundaries (HW/SW, COTS, org/subcontract, human ConOps); subtract-and-operate as applicable.",
        ),
    ]

    per_category: Dict[str, Any] = {}
    for key, title, guidance in category_specs:
        r = _evaluate_category(
            client=client,
            category_key=key,
            category_title=title,
            category_guidance=guidance,
            ours=ours,
            baseline=baseline,
            model=model,
        )
        per_category[key] = {
            "ours": r.get("ours"),
            "baseline": r.get("baseline"),
            "na_allowed": True,
            "evidence": r.get("evidence", ""),
        }

    ours_total = _sum_scores(per_category, side="ours")
    baseline_total = _sum_scores(per_category, side="baseline")
    if ours_total > baseline_total:
        winner = "OURS"
    elif baseline_total > ours_total:
        winner = "BASELINE"
    else:
        winner = "TIE"

    return {
        "summary": {
            "winner": winner,
            "why": f"Score totals (excluding N/A): ours={ours_total}, baseline={baseline_total}",
            "ours_total_score": ours_total,
            "baseline_total_score": baseline_total,
        },
        "scores": per_category,
        "major_issues": {"ours": [], "baseline": []},
        "recommendations": {"improve_ours": [], "improve_baseline": []},
    }


def evaluate_two_output_files_and_save(
    *,
    ours_path: str | Path,
    baseline_path: str | Path,
    outdir: str | Path,
    run_id: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    ours = _read_json(ours_path)
    baseline = _read_json(baseline_path)

    evaluation = evaluate_two_outputs(ours=ours, baseline=baseline, model=model)

    payload: Dict[str, Any] = {
        "run_id": run_id,
        "inputs": {"ours_file": str(ours_path), "baseline_file": str(baseline_path)},
        "evaluation": evaluation,
    }

    file_path = save_run_json(payload=payload, outdir=outdir, filename_prefix="evaluation", run_id=run_id)
    payload["_output_file"] = str(file_path)
    return payload
