"""Split batch-export element JSON into per-element mock files (API shape).

Reproduces tests/mocks/make_mocks.py lines 72-95 (the file-writing part) without
needing the JVM/papermill pipeline, but first passes the export through the
``windstorm.common.export_adapter`` so the per-element mocks are in the API
query-result shape windstorm's walkers (``verify_tool`` / ``init_variables``)
consume:
- reads the merged element JSON (list of {payload, identity})
- adapts it to API shape keyed by @id (see adapter)
- writes <dir>/<@id>.json                    (always, when @id present)
- writes <dir>/<@type>_<declaredName>.json   (when @type + declaredName present)
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from windstorm.common.export_adapter import adapt  # noqa: E402


def split_export(export_path: str, out_dir: str) -> tuple[int, int]:
    with open(export_path) as f:
        elements = json.load(f)
    adapted = adapt(elements)  # dict keyed by @id -> API-shaped payload
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    named = 0
    for eid, payload in adapted.items():
        if "@id" not in payload:
            payload["@id"] = eid
        with open(os.path.join(out_dir, eid + ".json"), "w") as g:
            g.write(json.dumps(payload))
        written += 1
        if "@type" in payload and "declaredName" in payload:
            with open(
                os.path.join(
                    out_dir, payload["@type"] + "_" + payload["declaredName"] + ".json"
                ),
                "w",
            ) as g:
                g.write(json.dumps(payload))
            named += 1
    return written, named


if __name__ == "__main__":
    export_path = sys.argv[1]
    out_dir = sys.argv[2]
    w, n = split_export(export_path, out_dir)
    print(f"split {export_path} -> {out_dir}: {w} @id files, {n} named files")
