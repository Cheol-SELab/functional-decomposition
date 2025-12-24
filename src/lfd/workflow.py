from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .llm import LLMClient


@dataclass(frozen=True)
class DecompositionInputs:
    mission_system: str
    stakeholders: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    candidate_fr: str = ""
    risk_tailoring_factors: List[str] = field(default_factory=list)


@dataclass
class DecompositionRun:
    refined_fr: Optional[Dict[str, Any]] = None
    selected_dp: Optional[Dict[str, Any]] = None
    assigned_im: Optional[Dict[str, Any]] = None
    gate_review: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None


class DecompositionWorkflow:
    def __init__(
        self,
        *,
        llm: LLMClient,
        model: Optional[str] = None,
    ) -> None:
        self._llm = llm
        self._model = model

    def _repair_json(
        self,
        *,
        system: str,
        instruction: str,
        bad_json: Dict[str, Any],
        errors: List[str],
        schema_hint: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        user = (
            "TASK: Repair the JSON to satisfy the validation constraints.\n"
            "RULES:\n"
            "- Return JSON only.\n"
            "- Preserve intent; change as little as possible.\n"
            "INPUT:\n"
            f"- Instruction: {instruction}\n"
            f"- Validation errors: {errors}\n"
            f"- Current JSON: {bad_json}\n"
        )
        return self._llm.complete_json(system=system, user=user, schema_hint=schema_hint, model=self._model)

    def _is_str_list(self, v: Any) -> bool:
        return isinstance(v, list) and all(isinstance(x, str) for x in v)

    def _step1_schema_hint(self) -> Dict[str, Any]:
        return {
            "name": "step1_refine_fr",
            "strict": False,
            "schema": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "refined_fr": {"type": "string"},
                    "rationale": {"type": "string"},
                    "verification_idea": {"type": "string"},
                    "sub_frs": {"type": "array", "items": {"type": "string"}},
                    "is_atomic": {"type": "boolean"},
                },
            },
        }

    def _validate_step1_output(self, s1: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not isinstance(s1.get("refined_fr"), str) or not s1.get("refined_fr").strip():
            errors.append("refined_fr must be a non-empty string")
        if not isinstance(s1.get("rationale"), str):
            errors.append("rationale must be a string")
        if not isinstance(s1.get("verification_idea"), str):
            errors.append("verification_idea must be a string")
        if "sub_frs" in s1 and not self._is_str_list(s1.get("sub_frs")):
            errors.append("sub_frs must be a list of strings")
        if not isinstance(s1.get("is_atomic"), bool):
            errors.append("is_atomic must be a boolean")
        return errors

    def _step2_schema_hint(self) -> Dict[str, Any]:
        return {
            "name": "step2_select_dp",
            "strict": False,
            "schema": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "candidate_dps": {"type": "array", "items": {"type": "string"}},
                    "selected_dp": {"type": "string"},
                    "coupling_check": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {
                            "assessment": {"type": "string"},
                            "potential_sources": {"type": "array", "items": {"type": "string"}},
                            "notes": {"type": "string"},
                        },
                    },
                    "assumptions_risks": {"type": "array", "items": {"type": "string"}},
                    "recommended_revision": {"type": "string"},
                },
            },
        }

    def _validate_step2_output(self, s2: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not self._is_str_list(s2.get("candidate_dps")) or not s2.get("candidate_dps"):
            errors.append("candidate_dps must be a non-empty list of strings")
        if not isinstance(s2.get("selected_dp"), str) or not s2.get("selected_dp").strip():
            errors.append("selected_dp must be a non-empty string")
        cc = s2.get("coupling_check")
        if not isinstance(cc, dict):
            errors.append("coupling_check must be an object")
        else:
            assess = cc.get("assessment")
            if not isinstance(assess, str) or assess.strip().lower() not in ("pass", "fail"):
                errors.append("coupling_check.assessment must be 'Pass' or 'Fail'")
        if "assumptions_risks" in s2 and not self._is_str_list(s2.get("assumptions_risks")):
            errors.append("assumptions_risks must be a list of strings")
        return errors

    def _step3_schema_hint(self) -> Dict[str, Any]:
        return {
            "name": "step3_assign_im",
            "strict": False,
            "schema": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "im_boundary": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {
                            "name": {"type": "string"},
                            "scope": {"type": "string"},
                        },
                    },
                    "external_interfaces": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": True,
                            "properties": {
                                "name": {"type": "string"},
                                "direction": {"type": "string"},
                                "details": {"type": "string"},
                            },
                        },
                    },
                    "module_containment_scores": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": True,
                            "properties": {
                                "module": {"type": "string"},
                                "containment_score": {"type": "number"},
                                "diffusion_score": {"type": "number"},
                                "notes": {"type": "string"},
                            },
                        },
                    },
                    "ownership_candidate": {"type": "string"},
                    "containment_hypothesis": {"type": "string"},
                    "containment_risks": {"type": "array", "items": {"type": "string"}},
                    "recommended_revision": {"type": "string"},
                },
            },
        }

    def _step4_schema_hint(self) -> Dict[str, Any]:
        return {
            "name": "step4_gate_review",
            "strict": False,
            "schema": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "fr_dp_gate": {"type": "object", "additionalProperties": True},
                    "dp_im_gate": {"type": "object", "additionalProperties": True},
                    "fr_im_gate": {"type": "object", "additionalProperties": True},
                    "recommended_revisions": {"type": "array", "items": {"type": "string"}},
                },
            },
        }

    def _validate_step4_output(self, s4: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        for k in ("fr_dp_gate", "dp_im_gate", "fr_im_gate"):
            if not isinstance(s4.get(k), dict):
                errors.append(f"{k} must be an object")
        for gate_key in ("fr_dp_gate", "dp_im_gate", "fr_im_gate"):
            gate = s4.get(gate_key)
            if isinstance(gate, dict):
                if not isinstance(gate.get("pass"), bool):
                    errors.append(f"{gate_key}.pass must be boolean")
        if "recommended_revisions" in s4 and not self._is_str_list(s4.get("recommended_revisions")):
            errors.append("recommended_revisions must be a list of strings")
        return errors

    def _step5_schema_hint(self) -> Dict[str, Any]:
        return {
            "name": "step5_decision",
            "strict": False,
            "schema": {
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "decision": {"type": "string"},
                    "justification": {"type": "string"},
                    "next_level_sub_frs": {"type": "array", "items": {"type": "string"}},
                    "revise": {"type": "object", "additionalProperties": True},
                    "record": {"type": "object", "additionalProperties": True},
                },
            },
        }

    def _validate_step5_output(self, s5: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        decision = s5.get("decision")
        allowed = {"STOP", "ZIGZAG_DOWN", "REVISE_CURRENT_LEVEL"}
        if not isinstance(decision, str) or decision.strip().upper() not in allowed:
            errors.append(f"decision must be one of {sorted(allowed)}")
        if not isinstance(s5.get("justification"), str):
            errors.append("justification must be a string")
        if "next_level_sub_frs" in s5 and not self._is_str_list(s5.get("next_level_sub_frs")):
            errors.append("next_level_sub_frs must be a list of strings")
        return errors

    def _validate_step3_output(
        self,
        *,
        s3: Dict[str, Any],
        available_modules: List[str],
        known_interfaces: List[str],
    ) -> List[str]:
        errors: List[str] = []

        im_boundary = s3.get("im_boundary") if isinstance(s3.get("im_boundary"), dict) else {}
        im_name = im_boundary.get("name")
        if available_modules:
            if not isinstance(im_name, str) or im_name not in available_modules:
                errors.append(
                    f"im_boundary.name must be one of available_modules: {available_modules}. Got: {im_name!r}"
                )

        if known_interfaces:
            ext = s3.get("external_interfaces")
            if not isinstance(ext, list):
                errors.append("external_interfaces must be a list")
            else:
                for idx, item in enumerate(ext):
                    if not isinstance(item, dict):
                        errors.append(f"external_interfaces[{idx}] must be an object")
                        continue
                    nm = item.get("name")
                    if not isinstance(nm, str) or nm not in known_interfaces:
                        errors.append(
                            f"external_interfaces[{idx}].name must be in known_interfaces {known_interfaces}. Got: {nm!r}"
                        )

        return errors

    def _repair_step3_output(
        self,
        *,
        selected_dp: str,
        available_modules: List[str],
        known_interfaces: List[str],
        s3_bad: Dict[str, Any],
        errors: List[str],
    ) -> Dict[str, Any]:
        system = "ROLE: Architecture-to-implementation assistant."
        user = (
            "TASK: Repair the IM assignment JSON so it obeys the constraints.\n"
            "RULES:\n"
            "- Return JSON only.\n"
            "- The IM boundary name MUST be exactly one of available_modules.\n"
            "- Every external interface name MUST be exactly one of known_interfaces.\n"
            "- Keep any valid fields unchanged if possible; only fix invalid parts.\n"
            "INPUT:\n"
            f"- Selected DP: {selected_dp}\n"
            f"- available_modules: {available_modules}\n"
            f"- known_interfaces: {known_interfaces}\n"
            f"- Validation errors: {errors}\n"
            f"- Current JSON: {s3_bad}\n"
            "OUTPUT FORMAT (JSON): same schema as Step 3 output.\n"
        )
        return self._llm.complete_json(
            system=system,
            user=user,
            schema_hint=self._step3_schema_hint(),
            model=self._model,
        )

    def step1_refine_fr(self, inputs: DecompositionInputs) -> Dict[str, Any]:
        system = "ROLE: Systems engineer assistant."
        user = (
            "TASK: Refine the candidate FR to be atomic and solution-neutral.\n"
            "RULES:\n"
            "- If the FR contains multiple obligations (often signaled by 'and'/'or'), split into atomic sub-FRs.\n"
            "- Keep FR in the problem domain (what), avoid implementation/technology (how).\n"
            "CONTEXT:\n"
            f"- Mission/System: {inputs.mission_system}\n"
            f"- Stakeholders: {', '.join(inputs.stakeholders) if inputs.stakeholders else '<none>'}\n"
            f"- Constraints: {', '.join(inputs.constraints) if inputs.constraints else '<none>'}\n"
            "INPUT:\n"
            f"- Candidate FR: {inputs.candidate_fr}\n"
            "OUTPUT FORMAT (JSON):\n"
            "{\n"
            '  "refined_fr": "...",\n'
            '  "rationale": "...",\n'
            '  "verification_idea": "...",\n'
            '  "sub_frs": ["..."],\n'
            '  "is_atomic": true\n'
            "}\n"
        )
        s1 = self._llm.complete_json(system=system, user=user, schema_hint=self._step1_schema_hint(), model=self._model)
        errors = self._validate_step1_output(s1)
        if errors:
            s1 = self._repair_json(
                system=system,
                instruction="Step 1 (Define/Refine FR)",
                bad_json=s1,
                errors=errors,
                schema_hint=self._step1_schema_hint(),
            )
        return s1

    def step2_select_dp(self, *, refined_fr: str, constraints_assumptions: List[str]) -> Dict[str, Any]:
        system = "ROLE: Architect assistant."
        user = (
            "TASK: Propose candidate DPs and evaluate FR<->DP mapping quality.\n"
            "RULES:\n"
            "- Keep DPs solution-neutral at this level (avoid naming specific technologies like sensors, vendors, protocols) unless the constraints explicitly force it.\n"
            "- Prefer logical solution concepts and boundaries that support independence (avoid coupled designs).\n"
            "INPUT:\n"
            f"- FR (refined): {refined_fr}\n"
            f"- Known constraints/assumptions: {', '.join(constraints_assumptions) if constraints_assumptions else '<none>'}\n"
            "OUTPUT FORMAT (JSON):\n"
            "{\n"
            '  "candidate_dps": ["..."],\n'
            '  "selected_dp": "...",\n'
            '  "coupling_check": {"assessment": "Pass|Fail", "potential_sources": ["..."], "notes": "..."},\n'
            '  "assumptions_risks": ["..."] ,\n'
            '  "recommended_revision": "..."\n'
            "}\n"
        )
        s2 = self._llm.complete_json(
            system=system,
            user=user,
            schema_hint=self._step2_schema_hint(),
            model=self._model,
        )
        errors = self._validate_step2_output(s2)
        if errors:
            s2 = self._repair_json(
                system=system,
                instruction="Step 2 (Select DP)",
                bad_json=s2,
                errors=errors,
                schema_hint=self._step2_schema_hint(),
            )
        return s2

    def step3_assign_im(self, *, selected_dp: str, available_modules: List[str], known_interfaces: List[str]) -> Dict[str, Any]:
        system = "ROLE: Architecture-to-implementation assistant."
        user = (
            "TASK: Propose a module boundary (IM) that contains the selected DP.\n"
            "RULES:\n"
            "- The IM boundary name MUST be chosen from the provided module list exactly (no inventing new module names).\n"
            "- External interfaces MUST be chosen from the provided interface list (no inventing new interfaces).\n"
            "- Evaluate containment against ALL candidate modules: for each module, estimate how well it would contain the DP (cohesion) and how much the DP would diffuse outside it (coupling).\n"
            "- Prefer the MOST SPECIFIC boundary that still contains the DP well. Avoid overly broad boundaries unless no narrower boundary can contain the DP without major diffusion.\n"
            "- If containment is weak for all modules, propose a revision to DP choice that improves containment without becoming implementation-specific.\n"
            "INPUT:\n"
            f"- Selected DP: {selected_dp}\n"
            f"- Candidate system elements/modules available: {', '.join(available_modules) if available_modules else '<unknown>'}\n"
            f"- Known interfaces: {', '.join(known_interfaces) if known_interfaces else '<unknown>'}\n"
            "OUTPUT FORMAT (JSON):\n"
            "{\n"
            '  "im_boundary": {"name": "...", "scope": "..."},\n'
            '  "external_interfaces": [{"name": "...", "direction": "in|out|inout", "details": "..."}],\n'
            '  "module_containment_scores": [{"module": "...", "containment_score": 0, "diffusion_score": 0, "notes": "..."}],\n'
            '  "ownership_candidate": "...",\n'
            '  "containment_hypothesis": "...",\n'
            '  "containment_risks": ["..."],\n'
            '  "recommended_revision": ""\n'
            "}\n"
        )
        s3 = self._llm.complete_json(
            system=system,
            user=user,
            schema_hint=self._step3_schema_hint(),
            model=self._model,
        )

        errors = self._validate_step3_output(
            s3=s3,
            available_modules=available_modules,
            known_interfaces=known_interfaces,
        )
        if errors:
            s3 = self._repair_step3_output(
                selected_dp=selected_dp,
                available_modules=available_modules,
                known_interfaces=known_interfaces,
                s3_bad=s3,
                errors=errors,
            )
        return s3

    def step4_gate_review(self, *, fr: str, dp: str, im: Dict[str, Any]) -> Dict[str, Any]:
        system = "ROLE: Gate reviewer."
        user = (
            "TASK: Evaluate the mapping quality at the current level.\n"
            "RULES:\n"
            "- Ground verifiability in the provided constraints/acceptance criteria where possible.\n"
            "- If a DP appears scattered across multiple responsibilities or interfaces, flag as diffusion risk (DP↔IM bridge).\n"
            "INPUT:\n"
            f"- FR: {fr}\n"
            f"- DP: {dp}\n"
            f"- IM boundary + interfaces: {im}\n"
            "OUTPUT FORMAT (JSON):\n"
            "{\n"
            '  "fr_dp_gate": {"pass": true, "reason": "..."},\n'
            '  "dp_im_gate": {"pass": true, "diffusion_risks": ["..."], "containment_notes": "..."},\n'
            '  "fr_im_gate": {"pass": true, "verification_feasibility": "...", "allocation_clarity": "..."},\n'
            '  "recommended_revisions": ["..."]\n'
            "}\n"
        )
        s4 = self._llm.complete_json(
            system=system,
            user=user,
            schema_hint=self._step4_schema_hint(),
            model=self._model,
        )
        errors = self._validate_step4_output(s4)
        if errors:
            s4 = self._repair_json(
                system=system,
                instruction="Step 4 (Gate Review)",
                bad_json=s4,
                errors=errors,
                schema_hint=self._step4_schema_hint(),
            )
        return s4

    def step5_decision(self, *, gate_results: Dict[str, Any], risk_tailoring_factors: List[str]) -> Dict[str, Any]:
        system = "ROLE: Decomposition controller."
        user = (
            "TASK: Decide whether to stop or derive next-level sub-FRs.\n"
            "INPUT:\n"
            f"- Gate results (Step 4): {gate_results}\n"
            f"- Risk tailoring factors: {', '.join(risk_tailoring_factors) if risk_tailoring_factors else '<none>'}\n"
            "OUTPUT FORMAT (JSON):\n"
            "{\n"
            '  "decision": "STOP|ZIGZAG_DOWN|REVISE_CURRENT_LEVEL",\n'
            '  "justification": "...",\n'
            '  "next_level_sub_frs": ["..."],\n'
            '  "revise": {"target": "FR|DP|IM", "why": "..."},\n'
            '  "record": {"assumptions": ["..."], "open_risks": ["..."], "evidence_needed": ["..."]}\n'
            "}\n"
        )
        s5 = self._llm.complete_json(
            system=system,
            user=user,
            schema_hint=self._step5_schema_hint(),
            model=self._model,
        )
        errors = self._validate_step5_output(s5)
        if errors:
            s5 = self._repair_json(
                system=system,
                instruction="Step 5 (Decision)",
                bad_json=s5,
                errors=errors,
                schema_hint=self._step5_schema_hint(),
            )
        return s5

    def run_one_level(
        self,
        *,
        inputs: DecompositionInputs,
        available_modules: Optional[List[str]] = None,
        known_interfaces: Optional[List[str]] = None,
    ) -> DecompositionRun:
        run = DecompositionRun()

        s1 = self.step1_refine_fr(inputs)
        run.refined_fr = s1

        refined_fr = str(s1.get("refined_fr", ""))
        s2 = self.step2_select_dp(refined_fr=refined_fr, constraints_assumptions=inputs.constraints)
        run.selected_dp = s2

        selected_dp = str(s2.get("selected_dp", ""))
        s3 = self.step3_assign_im(
            selected_dp=selected_dp,
            available_modules=available_modules or [],
            known_interfaces=known_interfaces or [],
        )
        run.assigned_im = s3

        s4 = self.step4_gate_review(fr=refined_fr, dp=selected_dp, im=s3)
        run.gate_review = s4

        s5 = self.step5_decision(gate_results=s4, risk_tailoring_factors=inputs.risk_tailoring_factors)
        run.decision = s5

        return run
