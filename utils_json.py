from __future__ import annotations
from dataclasses import asdict, is_dataclass
from typing import Any
import numpy as np

def to_jsonable(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (str, int, float, bool)):
        return x
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, complex):
        return {"re": float(x.real), "im": float(x.imag)}
    if is_dataclass(x):
        return to_jsonable(asdict(x))
    if isinstance(x, dict):
        return {str(k): to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [to_jsonable(v) for v in x]
    return str(x)

def ensure_summary_dict(summary: Any) -> dict:
    if summary is None:
        return {}
    if isinstance(summary, dict):
        return to_jsonable(summary)
    if isinstance(summary, str):
        return {"summary": summary}
    return {"summary": str(summary)}
import numpy as np
from typing import Any, Dict

def ensure_summary_dict(summary: Any) -> Dict[str, Any]:
    """Ensure the input is a JSON-serializable dictionary."""
    if isinstance(summary, dict):
        new_dict = {}
        for k, v in summary.items():
            if isinstance(v, (np.integer, int)):
                new_dict[k] = int(v)
            elif isinstance(v, (np.floating, float)):
                new_dict[k] = float(v)
            elif isinstance(v, np.ndarray):
                new_dict[k] = v.tolist()
            else:
                new_dict[k] = str(v)
        return new_dict
    return {"raw_summary": str(summary)}
