"""Parallel Bank Transactions & Fraud Detection demo."""

from __future__ import annotations

import multiprocessing as mp
from typing import Dict, List

from checker import build_correctness_report
from performance import append_speedup_efficiency
from plotting import generate_all_plots
from runners import run_processes, run_serial, run_threads
from transaction_generator import generate_initial_balances, generate_transactions


def _mode_title(mode: str) -> str:
    mapping = {
        "serial": "SERIAL",
        "threads_no_lock": "THREADS (NO LOCK)",
        "threads_lock": "THREADS (LOCK)",
        "processes_no_lock": "PROCESSES (NO LOCK)",
        "processes_lock": "PROCESSES (LOCK)",
    }
    return mapping.get(mode, mode.upper())


def _has_issue(row: Dict) -> bool:
    return row["mismatched_accounts"] > 0 or row["negative_accounts"] > 0


def _is_expected_race_case(row: Dict) -> bool:
    return row["mode"].endswith("no_lock") and int(row["workers"]) > 1 and _has_issue(row)


def _is_unexpected_failure(row: Dict) -> bool:
    if row["mode"].endswith("no_lock") and int(row["workers"]) > 1:
        # These runs are intentionally racy; mismatches are expected.
        return False
    return _has_issue(row)


def _print_result(row: Dict) -> None:
    if _is_expected_race_case(row):
        status = "RACE DETECTED (EXPECTED)"
    elif _is_unexpected_failure(row):
        status = "FAIL (UNEXPECTED)"
    else:
        status = "PASS"
    print(
        f"[{_mode_title(row['mode'])} | workers={row['workers']}] "
        f"runtime={row['runtime']:.4f}s, "
        f"negatives={row['negative_accounts']}, "
        f"mismatched={row['mismatched_accounts']}, "
        f"abs_error={row['total_abs_error']:.2f}, "
        f"fraud_flags={row['fraud_flags_count']}, "
        f"correctness={status}"
    )


def _to_row(result: Dict, baseline_balances: Dict[int, float]) -> Dict:
    report = build_correctness_report(
        baseline_balances=baseline_balances,
        candidate_balances=result["balances"],
    )
    return {
        "mode": result["mode"],
        "workers": result["workers"],
        "runtime": result["runtime"],
        "negative_accounts": report["negative_accounts"],
        "mismatched_accounts": report["mismatched_accounts"],
        "total_abs_error": report["total_abs_error"],
        "fraud_flags_count": len(result["fraud_flags"]),
    }


def run_all_modes() -> List[Dict]:
    # Tuned to make race conditions visible while keeping total runtime reasonable.
    num_accounts = 160
    num_transactions = 5_000
    workers_list = [1, 2, 4, 8]
    queue_size = 1_024

    amount_threshold = 3_500.0
    rapid_window = 0.01
    race_delay = 0.0008

    balances_seed = 123
    tx_seed = 456

    # High initial balances + moderate transaction amounts reduce failed withdrawals,
    # which keeps locked parallel runs behaviorally aligned with serial order.
    initial_balances = generate_initial_balances(
        num_accounts=num_accounts,
        seed=balances_seed,
        min_balance=90_000.0,
        max_balance=140_000.0,
    )
    transactions = generate_transactions(
        num_transactions=num_transactions,
        account_ids=initial_balances.keys(),
        seed=tx_seed,
        min_amount=10.0,
        max_amount=1_200.0,
    )

    print("Running Parallel Bank Transactions & Fraud Detection System")
    print(f"Accounts={num_accounts}, Transactions={num_transactions}")
    print(f"Workers tested={workers_list}")
    print("-" * 90)

    serial_result = run_serial(
        transactions=transactions,
        initial_balances=initial_balances,
        amount_threshold=amount_threshold,
        rapid_window=rapid_window,
    )
    baseline_balances = serial_result["balances"]

    rows: List[Dict] = []
    serial_row = _to_row(serial_result, baseline_balances)
    rows.append(serial_row)
    _print_result(serial_row)

    for workers in workers_list:
        result = run_threads(
            transactions=transactions,
            initial_balances=initial_balances,
            num_workers=workers,
            use_lock=False,
            queue_size=queue_size,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            race_delay=race_delay,
        )
        row = _to_row(result, baseline_balances)
        rows.append(row)
        _print_result(row)

        result = run_threads(
            transactions=transactions,
            initial_balances=initial_balances,
            num_workers=workers,
            use_lock=True,
            queue_size=queue_size,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            race_delay=race_delay,
        )
        row = _to_row(result, baseline_balances)
        rows.append(row)
        _print_result(row)

    for workers in workers_list:
        result = run_processes(
            transactions=transactions,
            initial_balances=initial_balances,
            num_workers=workers,
            use_lock=False,
            queue_size=queue_size,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            race_delay=race_delay,
        )
        row = _to_row(result, baseline_balances)
        rows.append(row)
        _print_result(row)

        result = run_processes(
            transactions=transactions,
            initial_balances=initial_balances,
            num_workers=workers,
            use_lock=True,
            queue_size=queue_size,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            race_delay=race_delay,
        )
        row = _to_row(result, baseline_balances)
        rows.append(row)
        _print_result(row)

    rows = append_speedup_efficiency(rows=rows, serial_runtime=serial_result["runtime"])

    print("-" * 90)
    print("Performance (Speedup Sp = T_serial / T_parallel, Efficiency Ep = Sp / p):")
    for row in rows:
        print(
            f"{_mode_title(row['mode']):<22} "
            f"p={row['workers']:<2} "
            f"time={row['runtime']:.4f}s "
            f"Sp={row['speedup']:.3f} "
            f"Ep={row['efficiency']:.3f}"
        )

    plot_files = generate_all_plots(
        rows=rows,
        baseline_fraud_flags=serial_result["fraud_flags"],
        output_dir="outputs",
    )

    print("-" * 90)
    unexpected_failures = [row for row in rows if _is_unexpected_failure(row)]
    expected_race_cases = [row for row in rows if _is_expected_race_case(row)]
    print(
        "Correctness summary: "
        f"{len(expected_race_cases)} expected race-case runs, "
        f"{len(unexpected_failures)} unexpected failures."
    )
    if unexpected_failures:
        print("Unexpected failing modes:")
        for row in unexpected_failures:
            print(f"- {_mode_title(row['mode'])} (workers={row['workers']})")

    print("-" * 90)
    print("Generated plots:")
    for path in plot_files:
        print(f"- {path}")

    return rows


if __name__ == "__main__":
    # Keep Windows multiprocessing behavior explicit and deterministic.
    mp.freeze_support()
    all_rows = run_all_modes()
    if any(_is_unexpected_failure(row) for row in all_rows):
        raise SystemExit(1)
