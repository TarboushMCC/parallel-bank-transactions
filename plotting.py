"""Matplotlib plotting utilities for project outputs."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib.pyplot as plt


MODE_LABELS = {
    "threads_no_lock": "Threads (No Lock)",
    "threads_lock": "Threads (Lock)",
    "processes_no_lock": "Processes (No Lock)",
    "processes_lock": "Processes (Lock)",
}


def _series(rows: Sequence[Dict], mode: str, metric: str) -> Tuple[List[int], List[float]]:
    points = [
        (int(r["workers"]), float(r[metric]))
        for r in rows
        if r["mode"] == mode and r["mode"] != "serial"
    ]
    points.sort(key=lambda x: x[0])
    return [p[0] for p in points], [p[1] for p in points]


def plot_speedup(rows: Sequence[Dict], output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    for mode in ("threads_no_lock", "threads_lock", "processes_no_lock", "processes_lock"):
        xs, ys = _series(rows, mode, "speedup")
        if xs:
            ax.plot(xs, ys, marker="o", linewidth=2, label=MODE_LABELS[mode])
    ax.set_title("Speedup vs Number of Workers")
    ax.set_xlabel("Workers")
    ax.set_ylabel("Speedup")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()
    output_path = output_dir / "speedup_vs_workers.png"
    fig.savefig(output_path, dpi=130)
    plt.close(fig)
    return output_path


def plot_efficiency(rows: Sequence[Dict], output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    for mode in ("threads_no_lock", "threads_lock", "processes_no_lock", "processes_lock"):
        xs, ys = _series(rows, mode, "efficiency")
        if xs:
            ax.plot(xs, ys, marker="o", linewidth=2, label=MODE_LABELS[mode])
    ax.set_title("Efficiency vs Number of Workers")
    ax.set_xlabel("Workers")
    ax.set_ylabel("Efficiency")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()
    output_path = output_dir / "efficiency_vs_workers.png"
    fig.savefig(output_path, dpi=130)
    plt.close(fig)
    return output_path


def plot_mismatch_comparison(rows: Sequence[Dict], output_dir: Path) -> Path:
    workers = sorted({int(r["workers"]) for r in rows if r["mode"] != "serial"})
    idx = list(range(len(workers)))
    width = 0.38

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)

    # Threads mismatch comparison
    thread_no_lock = [
        next(
            float(r["mismatched_accounts"])
            for r in rows
            if r["mode"] == "threads_no_lock" and int(r["workers"]) == w
        )
        for w in workers
    ]
    thread_lock = [
        next(
            float(r["mismatched_accounts"])
            for r in rows
            if r["mode"] == "threads_lock" and int(r["workers"]) == w
        )
        for w in workers
    ]
    axes[0].bar([i - width / 2 for i in idx], thread_no_lock, width=width, label="No Lock")
    axes[0].bar([i + width / 2 for i in idx], thread_lock, width=width, label="Lock")
    axes[0].set_title("Threads: Mismatch")
    axes[0].set_xticks(idx)
    axes[0].set_xticklabels(workers)
    axes[0].set_xlabel("Workers")
    axes[0].set_ylabel("Mismatched Accounts")
    axes[0].legend()

    # Processes mismatch comparison
    proc_no_lock = [
        next(
            float(r["mismatched_accounts"])
            for r in rows
            if r["mode"] == "processes_no_lock" and int(r["workers"]) == w
        )
        for w in workers
    ]
    proc_lock = [
        next(
            float(r["mismatched_accounts"])
            for r in rows
            if r["mode"] == "processes_lock" and int(r["workers"]) == w
        )
        for w in workers
    ]
    axes[1].bar([i - width / 2 for i in idx], proc_no_lock, width=width, label="No Lock")
    axes[1].bar([i + width / 2 for i in idx], proc_lock, width=width, label="Lock")
    axes[1].set_title("Processes: Mismatch")
    axes[1].set_xticks(idx)
    axes[1].set_xticklabels(workers)
    axes[1].set_xlabel("Workers")
    axes[1].legend()

    fig.suptitle("Mismatch Comparison (No Lock vs Locked)")
    fig.tight_layout()
    output_path = output_dir / "mismatch_comparison.png"
    fig.savefig(output_path, dpi=130)
    plt.close(fig)
    return output_path


def plot_fraud_flags_by_tx_type(fraud_flags: Sequence[Dict], output_dir: Path) -> Path:
    counts = Counter(flag.get("tx_type", "unknown") for flag in fraud_flags)
    tx_types = ["deposit", "withdraw", "transfer"]
    values = [counts.get(tx, 0) for tx in tx_types]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(tx_types, values)
    ax.set_title("Fraud Flags Count Per Transaction Type")
    ax.set_xlabel("Transaction Type")
    ax.set_ylabel("Flag Count")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    output_path = output_dir / "fraud_flags_by_tx_type.png"
    fig.savefig(output_path, dpi=130)
    plt.close(fig)
    return output_path


def generate_all_plots(
    rows: Sequence[Dict],
    baseline_fraud_flags: Sequence[Dict],
    output_dir: str = "outputs",
) -> List[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    files = [
        plot_speedup(rows, out),
        plot_efficiency(rows, out),
        plot_mismatch_comparison(rows, out),
        plot_fraud_flags_by_tx_type(baseline_fraud_flags, out),
    ]
    return files
