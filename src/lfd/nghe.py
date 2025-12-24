from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class CustomerRequirement:
    req_id: str
    title: str
    statement: str
    acceptance_criteria: str


_CR_HEADER_RE = re.compile(r"^\-\s+\*\*(CR\-NGHE\-\d{3})\s*\(([^)]+)\)\*\*\s*$")
_FIELD_RE = re.compile(r"^\s+\-\s+\*\*(Statement|Acceptance criteria)\*\*:\s*(.*)\s*$")


def parse_nghe_customer_requirements(markdown: str) -> List[CustomerRequirement]:
    lines = markdown.splitlines()

    out: List[CustomerRequirement] = []
    i = 0
    while i < len(lines):
        m = _CR_HEADER_RE.match(lines[i].rstrip())
        if not m:
            i += 1
            continue

        req_id = m.group(1).strip()
        title = m.group(2).strip()

        statement: Optional[str] = None
        acceptance: Optional[str] = None

        i += 1
        while i < len(lines):
            line = lines[i].rstrip()
            if _CR_HEADER_RE.match(line):
                break
            fm = _FIELD_RE.match(line)
            if fm:
                field = fm.group(1)
                value = fm.group(2).strip()
                if field == "Statement":
                    statement = value
                elif field == "Acceptance criteria":
                    acceptance = value
            i += 1

        out.append(
            CustomerRequirement(
                req_id=req_id,
                title=title,
                statement=statement or "",
                acceptance_criteria=acceptance or "",
            )
        )

    return out


def load_nghe_customer_requirements(path: str | Path) -> List[CustomerRequirement]:
    p = Path(path)
    return parse_nghe_customer_requirements(p.read_text(encoding="utf-8"))


def find_cr(reqs: List[CustomerRequirement], req_id: str) -> CustomerRequirement:
    for r in reqs:
        if r.req_id == req_id:
            return r
    raise KeyError(f"Requirement not found: {req_id}")
