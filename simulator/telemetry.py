import argparse
import csv
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

random.seed(7)

TELECOM = {"router", "switch", "cell_tower"}

# (المتوسط, الانحراف) للسلوك الطبيعي لكل قياس
PROFILES = {
    "telecom": {
        "temperature_c": (45, 3),
        "cpu_pct": (35, 8),
        "latency_ms": (20, 4),
        "packet_loss_pct": (0.3, 0.1),
    },
    "industrial": {
        "temperature_c": (60, 4),
        "vibration_mm_s": (2.0, 0.4),
        "load_pct": (55, 10),
    },
}

# كام بتزيد كل قراءة بعد ما العطل يبدأ
DRIFT = {
    "temperature_c": 0.15,
    "cpu_pct": 0.4,
    "latency_ms": 0.5,
    "packet_loss_pct": 0.05,
    "vibration_mm_s": 0.08,
    "load_pct": 0.3,
}


def load_assets(path="data/assets.csv"):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pick_faulty(assets, ticks, ratio=0.1):
    """يختار 10% من الأجهزة ويحدد لحظة بداية العطل لكل واحد."""
    chosen = random.sample(assets, int(len(assets) * ratio))
    return {
        a["asset_id"]: random.randint(int(ticks * 0.3), int(ticks * 0.6))
        for a in chosen
    }


def make_reading(asset, tick, fault_start):
    kind = "telecom" if asset["asset_type"] in TELECOM else "industrial"
    metrics = {}
    for name, (mean, std) in PROFILES[kind].items():
        value = random.gauss(mean, std)
        if fault_start is not None and tick >= fault_start:
            value += DRIFT[name] * (tick - fault_start)
        metrics[name] = round(max(value, 0), 2)
    return metrics


def corrupt(metrics):
    """يبوّظ قياس واحد: يا ناقص (None) يا قراءة غلط (-999)."""
    name = random.choice(list(metrics))
    metrics[name] = None if random.random() < 0.5 else -999.0


def generate_events(assets, ticks, faulty, step_seconds=10):
    start = datetime.now(timezone.utc) - timedelta(seconds=ticks * step_seconds)
    for tick in range(ticks):
        ts = start + timedelta(seconds=tick * step_seconds)
        for asset in assets:
            metrics = make_reading(asset, tick, faulty.get(asset["asset_id"]))
            if random.random() < 0.03:
                corrupt(metrics)
            event = {
                "event_id": str(uuid.uuid4()),
                "asset_id": asset["asset_id"],
                "event_ts": ts.isoformat(),
                **metrics,
            }
            yield event
            if random.random() < 0.01:
                yield event  # رسالة مكررة


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticks", type=int, default=200)
    args = parser.parse_args()

    assets = load_assets()
    faulty = pick_faulty(assets, args.ticks)

    out = Path("data/telemetry.jsonl")
    count = 0
    with out.open("w", encoding="utf-8") as f:
        for event in generate_events(assets, args.ticks, faulty):
            f.write(json.dumps(event) + "\n")
            count += 1

    Path("data/ground_truth.json").write_text(json.dumps(faulty, indent=2))
    print(f"Wrote {count} events to {out}")
    print(f"Injected faults into {len(faulty)} assets (see data/ground_truth.json)")