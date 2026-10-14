import csv
import json
from pathlib import Path

assets = list(csv.DictReader(open("data/assets.csv", encoding="utf-8")))
assert len(assets) == 60, f"expected 60 assets, got {len(assets)}"

events = [json.loads(line) for line in open("data/telemetry.jsonl", encoding="utf-8")]
unique_ids = {e["event_id"] for e in events}
assert len(unique_ids) == 60 * 200, f"expected 12000 unique events, got {len(unique_ids)}"
assert len(events) > len(unique_ids), "no duplicate events were injected"

truth = json.loads(Path("data/ground_truth.json").read_text(encoding="utf-8"))
assert len(truth) == 6, f"expected 6 injected faults, got {len(truth)}"

print(f"OK: {len(assets)} assets, {len(unique_ids)} unique events "
      f"({len(events) - len(unique_ids)} duplicates), {len(truth)} faults")
