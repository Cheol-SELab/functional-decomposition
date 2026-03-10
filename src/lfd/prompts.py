from __future__ import annotations

DOMAIN_CONTEXT = (
    "### DOMAIN CONTEXT (FR -> DP -> IM):\n"
    "A rigorous approach to functional decomposition requires understanding that system design "
    "operates across distinct but interconnected domains at every level of the hierarchy. "
    "In classic Axiomatic Design, the foundational mapping is between the functional domain (FR) "
    "and the physical/design domain (DP), with further linkage to realization variables. "
    "We adopt the FR -> DP mapping and introduce an explicit implementation/module layer (IM) "
    "to make architectural packaging and ownership boundaries analyzable for both physical and "
    "software-intensive systems.\n\n"
    "### FR -> DP -> IM\n\n"
    "- FR (Functional Requirement): Defines what the system must do. "
    "This is the problem statement expressed in the functional domain.\n"
    "- DP (Design Parameter): Specifies how to solve the requirement logically. "
    "This is the solution concept in the design domain.\n"
    "- IM (Implementation Module): Denotes where the selected DP is realized as an owned module boundary "
    "(physical component or software artifact). This is an explicit architectural layer introduced to reason "
    "about realization packaging, interfaces, and diffusion.\n\n"
    "Implementation modules can be physical components (e.g., motor assemblies, circuit boards, mechanical linkages) "
    "or software artifacts (e.g., class files, microservices, database instances, containers). "
    "The critical insight is that the distinction between DP and IM matters: one can have correct logic (DP) "
    "but poor architectural packaging (IM), such as duplicating an algorithm across multiple code files "
    "instead of centralizing it in a single module.\n"
)

EVALUATION_CRITERIA = (
    "EVALUATION CRITERIA (Stopping-Method Taxonomy):\n"
    "1. Pure FR: Atomicity (single obligation), solution-neutrality (problem domain only), testability.\n"
    "2. FR<->DP Bridge: Independence Axiom (uncoupled/decoupled design), Information Axiom (minimize complexity), "
    "coupling awareness, what-vs-how boundary.\n"
    "3. DP<->IM Bridge: Module containment (DP realized within IM boundary), diffusion/scattering risk "
    "(DP logic spread across multiple modules).\n"
    "4. Pure IM: Structural modularity evidence (cohesion, stability, clustering).\n"
    "5. FR<->IM Bridge: Verifiability at IM boundary, allocation boundaries "
    "(HW/SW, COTS, org/subcontract, human ConOps).\n"
)
