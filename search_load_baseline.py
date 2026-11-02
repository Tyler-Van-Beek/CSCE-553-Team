from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


def percentile(sorted_ms: list[float], p: float) -> float:
    if not sorted_ms:
        return float("nan")
    k = (len(sorted_ms) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_ms) - 1)
    if f == c:
        return sorted_ms[f]
    return sorted_ms[f] + (sorted_ms[c] - sorted_ms[f]) * (k - f)


def once(
    url: str,
    headers: dict[str, str],
    timeout: float,
) -> tuple[float, int, str]:
    req = urllib.request.Request(url, headers=headers, method="GET")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            ms = (time.perf_counter() - t0) * 1000.0
            return ms, int(resp.status), ""
    except urllib.error.HTTPError as e:
        try:
            e.read()
        except Exception:
            pass
        ms = (time.perf_counter() - t0) * 1000.0
        return ms, int(e.code), "http"
    except Exception as e:
        ms = (time.perf_counter() - t0) * 1000.0
        return ms, 0, f"{type(e).__name__}: {e}"


def search_worker_loop(
    stop_at: float,
    base_url: str,
    query_param: str,
    queries: list[str],
    category_param: str,
    categories: list[str],
    headers: dict[str, str],
    timeout: float,
    samples: list[tuple[float, int, str]],
    lock: threading.Lock,
) -> None:
    """Worker loop that generates dynamic search URLs with query and category parameters."""
    parsed_base = urllib.parse.urlparse(base_url)
    base_query_dict = dict(urllib.parse.parse_qsl(parsed_base.query))

    while time.perf_counter() < stop_at:
        q = random.choice(queries)
        
        # Build the dynamic URL with parameters
        query_dict = base_query_dict.copy()
        query_dict[query_param] = q
        
        if categories:
            cat = random.choice(categories)
            query_dict[category_param] = cat

        new_query = urllib.parse.urlencode(query_dict)
        target_url = urllib.parse.urlunparse(parsed_base._replace(query=new_query))

        s = once(target_url, headers, timeout)
        with lock:
            samples.append(s)


def main() -> int:
    p = argparse.ArgumentParser(description="CSCE 553 M2 URL-parameter search & category load driver")
    p.add_argument("--base", required=True, help="Origin, no trailing slash (e.g., http://127.0.0.1:8000)")
    p.add_argument("--path", default="/search/", help="Search endpoint path")
    p.add_argument("--query", default="", help="Search query string, or comma-separated terms (e.g., 'educ,python')")
    p.add_argument("--queries-file", default="", help="Path to file with one search query per line")
    p.add_argument("--query-param", default="q", help="Query parameter name (default: q)")
    p.add_argument("--category", default="", help="Category string, or comma-separated categories (e.g., 'Education,Tech')")
    p.add_argument("--category-param", default="Category", help="Category parameter name (default: Category)")
    p.add_argument("--token", default=os.environ.get("M2_TOKEN", ""))
    p.add_argument("--no-auth", action="store_true")
    p.add_argument("--concurrency", type=int, default=4)
    p.add_argument("--duration", type=float, default=60.0, help="Measure window seconds")
    p.add_argument("--warmup", type=float, default=10.0)
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--label", default="search_run")
    p.add_argument("--out-dir", default="m2/results")
    p.add_argument("--raw", action="store_true", help="Write per-request CSV")
    args = p.parse_args()

    base = args.base.rstrip("/")
    headers = {"Accept": "application/json", "User-Agent": "csce553-m2"}
    if args.token and not args.no_auth:
        headers["Authorization"] = f"Token {args.token}"

    target_url = base + (args.path if args.path.startswith("/") else "/" + args.path)

    # Load search queries from argument or file
    queries = []
    if args.query:
        queries = [q.strip() for q in args.query.split(",") if q.strip()]
    elif args.queries_file and Path(args.queries_file).exists():
        with open(args.queries_file, "r", encoding="utf-8") as f:
            queries = [line.strip() for line in f if line.strip()]
    
    if not queries:
        queries = ["test", "error", "user", "api", "status", "data", "admin", "search", "config", "metrics"]
        print(f"No query or file provided. Using {len(queries)} default search terms.", file=sys.stderr)

    # Load categories if provided
    categories = []
    if args.category:
        categories = [c.strip() for c in args.category.split(",") if c.strip()]

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    def run_window(seconds: float) -> list[tuple[float, int, str]]:
        samples: list[tuple[float, int, str]] = []
        lock = threading.Lock()
        stop_at = time.perf_counter() + seconds
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futs = []
            for _ in range(args.concurrency):
                futs.append(
                    pool.submit(
                        search_worker_loop,
                        stop_at,
                        target_url,
                        args.query_param,
                        queries,
                        args.category_param,
                        categories,
                        headers,
                        args.timeout,
                        samples,
                        lock,
                    )
                )
            for f in as_completed(futs):
                f.result()
        return samples

    print(f"warmup {args.warmup}s  measure {args.duration}s  c={args.concurrency}  Search Target: {target_url}")
    run_window(args.warmup)
    t_wall0 = time.perf_counter()
    samples = run_window(args.duration)
    wall = time.perf_counter() - t_wall0

    lat = [s[0] for s in samples]
    oks = [s for s in samples if 200 <= s[1] < 400]
    errs = len(samples) - len(oks)
    lat.sort()
    row: dict[str, Any] = {
        "label": args.label,
        "env_note": target_url,
        "concurrency": args.concurrency,
        "duration_s": round(wall, 3),
        "attempts": len(samples),
        "successes": len(oks),
        "errors": errs,
        "rps_success": round(len(oks) / wall, 3) if wall else 0,
        "p50_ms": round(percentile(lat, 50), 2),
        "p95_ms": round(percentile(lat, 95), 2),
        "p99_ms": round(percentile(lat, 99), 2),
        "max_ms": round(lat[-1], 2) if lat else float("nan"),
        "error_rate": round(errs / len(samples), 4) if samples else 1.0,
    }
    summary_path = out / "summary.csv"
    write_header = not summary_path.exists()
    with summary_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            w.writeheader()
        w.writerow(row)

    if args.raw:
        raw_path = out / f"{args.label}.requests.csv"
        with raw_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["latency_ms", "status", "error"])
            w.writerows(samples)

    print(json.dumps(row, indent=2))
    if row["error_rate"] > 0.10:
        print("STOP RULE: error_rate > 10%", file=sys.stderr)
    if row["p99_ms"] == row["p99_ms"] and row["p99_ms"] > 5000:
        print("STOP RULE: p99_ms > 5000", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())