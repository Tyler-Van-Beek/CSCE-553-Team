from pathlib import Path
import csv

import matplotlib.pyplot as plt


M2_DIR = Path(__file__).resolve().parent
RESULTS_DIR = M2_DIR / "results"
SUMMARY_FILE = RESULTS_DIR / "summary.csv"

HOSTED_LABELS = {
    "H2-read-c1",
    "H2-read-c4",
    "H2-read-c8",
    "H2-read-c16",
    "H2-read-c32",
}
LOCAL_LABELS = {
    "L-read-c1",
    "L-read-c4",
}


def load_series(labels):
    with SUMMARY_FILE.open(newline="", encoding="utf-8") as stream:
        rows = [row for row in csv.DictReader(stream) if row["label"] in labels]

    rows.sort(key=lambda row: int(row["concurrency"]))
    return {
        "concurrency": [int(row["concurrency"]) for row in rows],
        "rps": [float(row["rps_success"]) for row in rows],
        "p50": [float(row["p50_ms"]) for row in rows],
        "p99": [float(row["p99_ms"]) for row in rows],
        "error_pct": [float(row["error_rate"]) * 100 for row in rows],
    }


def finish_chart(filename, ylabel, title):
    plt.xlabel("Offered concurrency (closed-loop clients)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xscale("log", base=2)
    plt.xticks([1, 4, 8, 16, 32], ["1", "4", "8", "16", "32"])
    plt.grid(True, which="major", linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / filename, dpi=180)
    plt.close()


def main():
    hosted = load_series(HOSTED_LABELS)
    local = load_series(LOCAL_LABELS)

    plt.figure(figsize=(8, 5))
    plt.plot(hosted["concurrency"], hosted["rps"], marker="o", label="Hosted API")
    plt.plot(local["concurrency"], local["rps"], marker="s", label="Local API")
    finish_chart(
        "throughput-vs-concurrency.png",
        "Successful throughput (requests/second)",
        "Read Throughput vs Offered Concurrency",
    )

    plt.figure(figsize=(8, 5))
    plt.plot(hosted["concurrency"], hosted["p50"], marker="o", label="Hosted p50")
    plt.plot(hosted["concurrency"], hosted["p99"], marker="o", label="Hosted p99")
    plt.plot(local["concurrency"], local["p50"], marker="s", label="Local p50")
    plt.plot(local["concurrency"], local["p99"], marker="s", label="Local p99")
    plt.axhline(5000, color="red", linestyle=":", label="5-second stop rule")
    finish_chart(
        "latency-vs-concurrency.png",
        "Latency (milliseconds)",
        "Read Latency vs Offered Concurrency",
    )

    plt.figure(figsize=(8, 5))
    plt.plot(hosted["concurrency"], hosted["error_pct"], marker="o", label="Hosted API")
    plt.plot(local["concurrency"], local["error_pct"], marker="s", label="Local API")
    plt.axhline(10, color="red", linestyle=":", label="10% stop rule")
    finish_chart(
        "error-rate-vs-concurrency.png",
        "Error rate (%)",
        "Read Error Rate vs Offered Concurrency",
    )

    print("Created:")
    for filename in (
        "throughput-vs-concurrency.png",
        "latency-vs-concurrency.png",
        "error-rate-vs-concurrency.png",
    ):
        print(RESULTS_DIR / filename)


if __name__ == "__main__":
    main()
