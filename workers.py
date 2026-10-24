"""Worker entry points for threaded and multiprocessing modes."""

from __future__ import annotations

from queue import Queue
from typing import Any, Optional

from transaction_engine import apply_transaction


def thread_worker(
    tx_queue: Queue,
    balances: Any,
    ledger: Any,
    fraud_flags: Any,
    last_seen_by_account: Any,
    lock: Optional[Any],
    simulate_race: bool,
    race_delay: float,
    amount_threshold: float,
    rapid_window: float,
    atomic_transfer: bool,
) -> None:
    while True:
        tx = tx_queue.get()
        if tx is None:
            tx_queue.task_done()
            break

        apply_transaction(
            tx=tx,
            balances=balances,
            ledger=ledger,
            fraud_flags=fraud_flags,
            last_seen_by_account=last_seen_by_account,
            lock=lock,
            simulate_race=simulate_race,
            race_delay=race_delay,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            atomic_transfer=atomic_transfer,
        )
        tx_queue.task_done()


def process_worker(
    tx_queue: Any,
    balances: Any,
    ledger: Any,
    fraud_flags: Any,
    last_seen_by_account: Any,
    lock: Optional[Any],
    simulate_race: bool,
    race_delay: float,
    amount_threshold: float,
    rapid_window: float,
    atomic_transfer: bool,
) -> None:
    while True:
        tx = tx_queue.get()
        if tx is None:
            break

        apply_transaction(
            tx=tx,
            balances=balances,
            ledger=ledger,
            fraud_flags=fraud_flags,
            last_seen_by_account=last_seen_by_account,
            lock=lock,
            simulate_race=simulate_race,
            race_delay=race_delay,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            atomic_transfer=atomic_transfer,
        )
