
import getpass
import json
import socket
from pathlib import Path

RESULTS = Path("dbt/target/run_results.json")
AUDIT_LOG = Path("data/audit/dbt_runs.jsonl")

data = json.loads(RESULTS.read_text(encoding="utf-8"))
meta = data["metadata"]

rows = []
for r in data["results"]:
    rows.append({
        "invocation_id": meta["invocation_id"],
        "run_at": meta["generated_at"],
        "dbt_version": meta["dbt_version"],
        "command": data.get("args", {}).get("which"),
        "executed_by": getpass.getuser(),
        "host": socket.gethostname(),
        "node": r["unique_id"],
        "status": r["status"],
        "seconds": round(r["execution_time"], 3),
        "failures": r.get("failures"),
    })

AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
with AUDIT_LOG.open("a", encoding="utf-8") as f:
    for row in rows:
        f.write(json.dumps(row) + "\n")

print(f"Logged {len(rows)} results for invocation {meta['invocation_id']}")