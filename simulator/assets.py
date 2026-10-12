import csv
import random
from pathlib import Path
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

CLIENTS = {
    "TelcoCo": ["router", "switch", "cell_tower"],
    "EnergyCo": ["transformer", "pump", "motor"],
    "GovNet": ["router", "switch"],
}
SITES = ["Cairo", "Alexandria", "Giza", "Mansoura", "Aswan"]
VENDORS = ["Cisco", "Huawei", "Siemens", "ABB", "Schneider"]


def generate_assets(n=60):
    assets = []
    for i in range(1, n + 1):
        client = random.choice(list(CLIENTS))
        assets.append({
            "asset_id": f"AST-{i:04d}",
            "client": client,
            "asset_type": random.choice(CLIENTS[client]),
            "site": random.choice(SITES),
            "vendor": random.choice(VENDORS),
            "install_date": fake.date_between(start_date="-8y", end_date="-1y").isoformat(),
            "owner_name": fake.name(),
            "owner_email": fake.email(),
        })
    return assets


if __name__ == "__main__":
    assets = generate_assets()
    out = Path("data/assets.csv")
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=assets[0].keys())
        writer.writeheader()
        writer.writerows(assets)
    print(f"Wrote {len(assets)} assets to {out}")