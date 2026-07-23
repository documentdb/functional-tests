"""
JSON rendering.

Serializes the analysis as machine-readable JSON, for ad-hoc tooling or
debugging. Presentation only; a peer of the text renderer.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict


def render(analysis: Dict[str, Any]) -> str:
    """Render the analysis as a JSON document."""
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": analysis["summary"],
        "by_tag": analysis["by_tag"],
        "tests": analysis["tests"],
    }
    return json.dumps(report, indent=2)
