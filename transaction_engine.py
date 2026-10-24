"""Core transaction operations and fraud detection."""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, Optional


def _involved_accounts(tx: dict) -> Iterable[int]:
    tx_type = tx["type"]
    if tx_type in ("deposit", "withdraw"):
        return [tx["account"]]
    if tx_type == "transfer":
        return [tx["src"], tx["dst"]]
    return []


def _detect_fraud(
    tx: dict,
    fraud_flags: Any,
    last_seen_by_account: Any,
    amount_threshold: float,
    rapid_window: float,
) -> None:
    tx_id = tx["id"]
    tx_type = tx["type"]
    amount = float(tx["amount"])
    ts = float(tx["ts"])

    if amount > amount_threshold:
        fraud_flags.append(
            {
                "tx_id": tx_id,
                "tx_type": tx_type,
                "reason": "amount_above_threshold",
                "amount": amount,
                "ts": ts,
            }
        )

    for account in _involved_accounts(tx):
        prev_ts = last_seen_by_account.get(account)
        if prev_ts is not None:
            dt = ts - float(prev_ts)
            if 0.0 <= dt <= rapid_window:
                fraud_flags.append(
                    {
                        "tx_id": tx_id,
                        "tx_type": tx_type,
                        "reason": "high_frequency_same_account",
                        "account": account,
                        "delta_t": dt,
                        "amount": amount,
                        "ts": ts,
                    }
                )
        last_seen_by_account[account] = ts


def _deposit(
    balances: Any,
    account_id: int,
    amount: float,
    simulate_race: bool,
    race_delay: float,
) -> bool:
    current = float(balances.get(account_id, 0.0))
    updated = current + amount
    if simulate_race:
        time.sleep(race_delay)
    balances[account_id] = round(updated, 2)
    return True


def _withdraw(
    balances: Any,
    account_id: int,
    amount: float,
    simulate_race: bool,
    race_delay: float,
) -> bool:
    current = float(balances.get(account_id, 0.0))
    if current < amount:
        return False
    updated = current - amount
    if simulate_race:
        time.sleep(race_delay)
    balances[account_id] = round(updated, 2)
    return True


def _transfer_non_atomic(
    balances: Any,
    src_account: int,
    dst_account: int,
    amount: float,
    simulate_race: bool,
    race_delay: float,
) -> bool:
    # Intentionally non-atomic path for no-lock execution modes.
    ok = _withdraw(
        balances=balances,
        account_id=src_account,
        amount=amount,
        simulate_race=simulate_race,
        race_delay=race_delay,
    )
    if not ok:
        return False
    _deposit(
        balances=balances,
        account_id=dst_account,
        amount=amount,
        simulate_race=simulate_race,
        race_delay=race_delay,
    )
    return True


def _transfer_atomic(balances: Any, src_account: int, dst_account: int, amount: float) -> bool:
    src_balance = float(balances.get(src_account, 0.0))
    if src_balance < amount:
        return False
    dst_balance = float(balances.get(dst_account, 0.0))
    balances[src_account] = round(src_balance - amount, 2)
    balances[dst_account] = round(dst_balance + amount, 2)
    return True


def _process_transaction_unlocked(
    tx: dict,
    balances: Any,
    ledger: Any,
    fraud_flags: Any,
    last_seen_by_account: Any,
    simulate_race: bool,
    race_delay: float,
    amount_threshold: float,
    rapid_window: float,
    atomic_transfer: bool,
) -> None:
    tx_type = tx["type"]
    amount = float(tx["amount"])
    success = False

    if tx_type == "deposit":
        success = _deposit(
            balances=balances,
            account_id=tx["account"],
            amount=amount,
            simulate_race=simulate_race,
            race_delay=race_delay,
        )
    elif tx_type == "withdraw":
        success = _withdraw(
            balances=balances,
            account_id=tx["account"],
            amount=amount,
            simulate_race=simulate_race,
            race_delay=race_delay,
        )
    elif tx_type == "transfer":
        if atomic_transfer:
            success = _transfer_atomic(
                balances=balances,
                src_account=tx["src"],
                dst_account=tx["dst"],
                amount=amount,
            )
        else:
            success = _transfer_non_atomic(
                balances=balances,
                src_account=tx["src"],
                dst_account=tx["dst"],
                amount=amount,
                simulate_race=simulate_race,
                race_delay=race_delay,
            )
    else:
        raise ValueError(f"Unknown transaction type: {tx_type}")

    ledger.append(
        {
            "tx_id": tx["id"],
            "tx_type": tx_type,
            "amount": amount,
            "status": "applied" if success else "rejected_insufficient_funds",
            "ts": tx["ts"],
        }
    )

    _detect_fraud(
        tx=tx,
        fraud_flags=fraud_flags,
        last_seen_by_account=last_seen_by_account,
        amount_threshold=amount_threshold,
        rapid_window=rapid_window,
    )


def apply_transaction(
    tx: dict,
    balances: Any,
    ledger: Any,
    fraud_flags: Any,
    last_seen_by_account: Any,
    *,
    lock: Optional[Any],
    simulate_race: bool,
    race_delay: float,
    amount_threshold: float,
    rapid_window: float,
    atomic_transfer: bool,
) -> None:
    if lock is None:
        _process_transaction_unlocked(
            tx=tx,
            balances=balances,
            ledger=ledger,
            fraud_flags=fraud_flags,
            last_seen_by_account=last_seen_by_account,
            simulate_race=simulate_race,
            race_delay=race_delay,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            atomic_transfer=atomic_transfer,
        )
        return

    with lock:
        _process_transaction_unlocked(
            tx=tx,
            balances=balances,
            ledger=ledger,
            fraud_flags=fraud_flags,
            last_seen_by_account=last_seen_by_account,
            simulate_race=False,
            race_delay=0.0,
            amount_threshold=amount_threshold,
            rapid_window=rapid_window,
            atomic_transfer=True,
        )
