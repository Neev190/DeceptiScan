"""
Load test for DeceptiScan /api/v1/analyze endpoint.

Simulates 5 concurrent users hammering the endpoint for 30 seconds.
Uses only stdlib concurrent.futures + requests (no Locust/etc).

Usage:
    python load_test.py [--url http://localhost:5000] [--workers 5] [--duration 30]
"""
import time
import statistics
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

PAYLOAD = {
    "content": (
        "Scientists at Harvard University have published a new study confirming that "
        "regular aerobic exercise significantly improves cardiovascular health and reduces "
        "the risk of heart disease by up to 35 percent. The research, conducted over a "
        "ten-year period with more than 50,000 participants, found that individuals who "
        "exercised at least 150 minutes per week had markedly lower rates of hypertension, "
        "stroke, and coronary artery disease compared to sedentary controls. The lead "
        "researcher stated that these findings reinforce existing public health guidelines "
        "on physical activity and should inform future clinical recommendations."
    )
}


def send_request(url: str, session: requests.Session) -> dict:
    """Send one POST /analyze request and return timing + status."""
    start = time.perf_counter()
    try:
        resp = session.post(
            f"{url}/api/v1/analyze",
            json=PAYLOAD,
            timeout=30,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "status": resp.status_code,
            "latency_ms": elapsed_ms,
            "error": None,
        }
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "status": 0,
            "latency_ms": elapsed_ms,
            "error": str(exc),
        }


def worker(url: str, stop_at: float, results: list) -> None:
    """Worker thread: keeps sending requests until stop_at epoch time."""
    with requests.Session() as session:
        while time.time() < stop_at:
            result = send_request(url, session)
            results.append(result)


def percentile(data: list, pct: float) -> float:
    """Return the pct-th percentile of data (0-100)."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100
    lo, hi = int(k), min(int(k) + 1, len(sorted_data) - 1)
    return sorted_data[lo] + (sorted_data[hi] - sorted_data[lo]) * (k - lo)


def main():
    parser = argparse.ArgumentParser(description="DeceptiScan load test")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL")
    parser.add_argument("--workers", type=int, default=5, help="Concurrent users")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")
    args = parser.parse_args()

    print(f"Starting load test: {args.workers} workers × {args.duration}s → {args.url}")
    print(f"Payload size: {len(PAYLOAD['content'])} chars")
    print("-" * 60)

    # Shared results list (GIL-safe for appends from threads)
    all_results: list = []
    stop_at = time.time() + args.duration

    start_wall = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [
            executor.submit(worker, args.url, stop_at, all_results)
            for _ in range(args.workers)
        ]
        for f in as_completed(futures):
            f.result()  # surface any unexpected thread exceptions
    wall_time = time.perf_counter() - start_wall

    # Analyse results
    total = len(all_results)
    errors = [r for r in all_results if r["status"] == 0 or r["status"] >= 400]
    successes = [r for r in all_results if 200 <= r["status"] < 300]
    latencies = [r["latency_ms"] for r in successes]

    error_count = len(errors)
    rps = total / wall_time if wall_time > 0 else 0

    p50 = percentile(latencies, 50) if latencies else 0
    p95 = percentile(latencies, 95) if latencies else 0
    p99 = percentile(latencies, 99) if latencies else 0
    mean = statistics.mean(latencies) if latencies else 0
    min_lat = min(latencies) if latencies else 0
    max_lat = max(latencies) if latencies else 0

    # Status code breakdown
    status_counts: dict = {}
    for r in all_results:
        key = r["status"] if r["status"] != 0 else "connection_error"
        status_counts[key] = status_counts.get(key, 0) + 1

    # Error details (first 5 unique errors)
    unique_errors = {}
    for r in errors:
        if r["error"] and r["error"] not in unique_errors:
            unique_errors[r["error"]] = 0
        if r["error"]:
            unique_errors[r["error"]] += 1

    print(f"\n{'='*60}")
    print(f"  LOAD TEST RESULTS")
    print(f"{'='*60}")
    print(f"  Duration (wall):    {wall_time:.1f}s")
    print(f"  Workers:            {args.workers}")
    print(f"  Total requests:     {total}")
    print(f"  Successful (2xx):   {len(successes)}")
    print(f"  Errors (non-2xx):   {error_count}")
    print(f"  Requests/sec:       {rps:.2f}")
    print(f"\n  Latency (2xx only, ms):")
    print(f"    min:  {min_lat:.0f}")
    print(f"    mean: {mean:.0f}")
    print(f"    p50:  {p50:.0f}")
    print(f"    p95:  {p95:.0f}")
    print(f"    p99:  {p99:.0f}")
    print(f"    max:  {max_lat:.0f}")
    print(f"\n  Status code breakdown:")
    for code, count in sorted(status_counts.items(), key=lambda x: str(x[0])):
        print(f"    {code}: {count}")
    if unique_errors:
        print(f"\n  Unique errors:")
        for err, count in unique_errors.items():
            print(f"    [{count}x] {err[:120]}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
