from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


def load_env_file(path: str | os.PathLike[str], *, override: bool = False) -> Dict[str, str]:
    p = Path(path)
    if not p.exists():
        return {}

    loaded: Dict[str, str] = {}
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        key = k.strip()
        val = v.strip().strip('"').strip("'")
        if not key:
            continue
        if not override and key in os.environ:
            continue
        os.environ[key] = val
        loaded[key] = val

    return loaded


def load_default_env(*, project_root: Optional[str | os.PathLike[str]] = None, override: bool = False) -> Dict[str, str]:
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
    return load_env_file(root / ".env", override=override)
