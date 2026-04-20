import argparse
import concurrent.futures
import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"


def send_request(client: httpx.Client, payload: dict) -> None:
    try:
        start = time.perf_counter()
        r = client.post(f"{BASE_URL}/chat", json=payload)
        latency = (time.perf_counter() - start) * 1000

        try:
            body = r.json()
        except Exception:
            body = {}

        correlation_id = body.get("correlation_id", "MISSING")
        feature = payload.get("feature", "unknown")

        print(f"[{r.status_code}] {correlation_id} | {feature} | {latency:.1f}ms")
    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c","--concurrency",
        type=int,
        default=1,
        help="Number of concurrent requests",
    )
    parser.add_argument(
        "-q","--queries",
        type=Path,
        default=Path("data/sample_queries.jsonl"),
        help="Path to JSONL file containing request payloads",
    )
    args = parser.parse_args()

    if not args.queries.exists():
        raise FileNotFoundError(f"Queries file not found: {args.queries}")

    lines = [
        line
        for line in args.queries.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    with httpx.Client(timeout=30.0) as client:
        if args.concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = [
                    executor.submit(send_request, client, json.loads(line))
                    for line in lines
                ]
                concurrent.futures.wait(futures)
        else:
            for line in lines:
                send_request(client, json.loads(line))


if __name__ == "__main__":
    main()