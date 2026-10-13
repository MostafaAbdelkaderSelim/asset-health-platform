import argparse
import json
import time

from confluent_kafka import Producer

TOPIC = "telemetry.raw"


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="data/telemetry.jsonl")
    parser.add_argument("--rate", type=float, default=500,
                        help="events per second (0 = as fast as possible)")
    args = parser.parse_args()

    producer = Producer({"bootstrap.servers": "localhost:19092"})
    sent = 0

    with open(args.file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            event = json.loads(line)
            producer.produce(
                TOPIC,
                key=event["asset_id"],
                value=line,
                callback=delivery_report,
            )
            producer.poll(0)
            sent += 1

            if args.rate > 0 and sent % 100 == 0:
                time.sleep(100 / args.rate)
            if sent % 2000 == 0:
                print(f"sent {sent} events")

    producer.flush()
    print(f"Done. Sent {sent} events to topic '{TOPIC}'")


if __name__ == "__main__":
    main()