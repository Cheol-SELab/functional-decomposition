from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, Optional


def save_run_json(
    *,
    payload: Dict[str, Any],
    outdir: str | Path,
    filename_prefix: str,
    run_id: Optional[str] = None,
) -> Path:
    out_path = Path(outdir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    rid = f"_{run_id}" if run_id else ""
    file_path = out_path / f"{filename_prefix}{rid}_{ts}.json"
    file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return file_path
