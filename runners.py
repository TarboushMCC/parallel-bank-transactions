"""Execution modes: serial, threads, and processes."""

from __future__ import annotations

import copy
import multiprocessing as mp
import threading
import time
from queue import Queue
from typing import Any, Dict, List

from transaction_engine import apply_transaction
from workers import process_worker, thread_worker


def run_serial(
    transactions: List[dict],
    initial_balances: Dict[int, float],
    amount_threshold: float,
    rapid_window: float,
) -> Dict[str, Any]:
    balances = copy.deepcopy(initial_balances)
    ledger: List[dict] = []
    fraud_flags: List[dict] = []
    last_seen_by_account: Dict[int, float] = {}

    start = time.time()
    for tx in transactions:
        apply_transaction(
            tx=tx,
            balances=balances,
            ledger=ledger,
            fraud_flags=fraud_flags,
            last_seen_by_account=last_seen_by_account,
            lock=None,
            simulate_race=False,
            race_delay=0.0,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            atomic_transfer=True,
        )
    runtime = time.time() - start

    return {
        "mode": "serial",
        "workers": 1,
        "runtime": runtime,
        "balances": balances,
        "ledger": ledger,
        "fraud_flags": fraud_flags,
    }


def run_threads(
    transactions: List[dict],
    initial_balances: Dict[int, float],
    num_workers: int,
    use_lock: bool,
    queue_size: int,
    amount_threshold: float,
    rapid_window: float,
    race_delay: float,
) -> Dict[str, Any]:
    balances = copy.deepcopy(initial_balances)
    ledger: List[dict] = []
    fraud_flags: List[dict] = []
    last_seen_by_account: Dict[int, float] = {}

    tx_queue: Queue = Queue(maxsize=queue_size)
    lock = threading.Lock() if use_lock else None
    simulate_race = not use_lock
    atomic_transfer = use_lock

    threads = []
    start = time.time()
    for _ in range(num_workers):
        t = threading.Thread(
            target=thread_worker,
            args=(
                tx_queue,
                balances,
                ledger,
                fraud_flags,
                last_seen_by_account,
                lock,
                simulate_race,
                race_delay,
                amount_threshold,
                rapid_window,
                atomic_transfer,
            ),
        )
        t.start()
        threads.append(t)

    for tx in transactions:
        tx_queue.put(tx)
    for _ in range(num_workers):
        tx_queue.put(None)

    tx_queue.join()
    for t in threads:
        t.join()
    runtime = time.time() - start

    mode = "threads_lock" if use_lock else "threads_no_lock"
    return {
        "mode": mode,
        "workers": num_workers,
        "runtime": runtime,
        "balances": balances,
        "ledger": ledger,
        "fraud_flags": fraud_flags,
    }


def run_processes(
    transactions: List[dict],
    initial_balances: Dict[int, float],
    num_workers: int,
    use_lock: bool,
    queue_size: int,
    amount_threshold: float,
    rapid_window: float,
    race_delay: float,
) -> Dict[str, Any]:
    manager = mp.Manager()
    balances = manager.dict(copy.deepcopy(initial_balances))
    ledger = manager.list()
    fraud_flags = manager.list()
    last_seen_by_account = manager.dict()

    tx_queue = mp.Queue(maxsize=queue_size)
    lock = mp.Lock() if use_lock else None
    simulate_race = not use_lock
    atomic_transfer = use_lock

    processes = []
    start = time.time()
    for _ in range(num_workers):
        p = mp.Process(
            target=process_worker,
            args=(
                tx_queue,
                balances,
                ledger,
                fraud_flags,
                last_seen_by_account,
                lock,
                simulate_race,
                race_delay,
                amount_threshold,
                rapid_window,
                atomic_transfer,
            ),
        )
        p.start()
        processes.append(p)

    for tx in transactions:
        tx_queue.put(tx)
    for _ in range(num_workers):
        tx_queue.put(None)

    for p in processes:
        p.join()
    runtime = time.time() - start

    tx_queue.close()
    tx_queue.join_thread()

    balances_out = {int(k): float(v) for k, v in balances.items()}
    ledger_out = list(ledger)
    fraud_flags_out = list(fraud_flags)
    manager.shutdown()

    mode = "processes_lock" if use_lock else "processes_no_lock"
    return {
        "mode": mode,
        "workers": num_workers,
        "runtime": runtime,
        "balances": balances_out,
        "ledger": ledger_out,
        "fraud_flags": fraud_flags_out,
    }
