"""Transaction and dataset generation utilities."""

from __future__ import annotations

import random
from typing import Dict, Iterable, List


def generate_initial_balances(
    num_accounts: int,
    seed: int = 42,
    min_balance: float = 2_000.0,
    max_balance: float = 10_000.0,
) -> Dict[int, float]:
    """Create deterministic starting balances for all accounts."""
    rng = random.Random(seed)
    balances = {}
    for account_id in range(1, num_accounts + 1):
        balances[account_id] = round(rng.uniform(min_balance, max_balance), 2)
    return balances


def _pick_account(rng: random.Random, all_accounts: List[int], hot_accounts: List[int]) -> int:
    """Pick a possibly contended account to increase race-condition visibility."""
    if rng.random() < 0.75:
        return rng.choice(hot_accounts)
    return rng.choice(all_accounts)


def generate_transactions(
    num_transactions: int,
    account_ids: Iterable[int],
    seed: int = 99,
    deposit_weight: float = 0.35,
    withdraw_weight: float = 0.35,
    transfer_weight: float = 0.30,
    min_amount: float = 5.0,
    max_amount: float = 6_000.0,
) -> List[dict]:
    """
    Generate deterministic transactions with mixed timing.

    The timestamp stream intentionally contains short gaps to trigger the
    "high-frequency activity" fraud rule.
    """
    rng = random.Random(seed)
    accounts = list(account_ids)
    if not accounts:
        return []

    hot_count = max(5, len(accounts) // 10)
    hot_accounts = accounts[:hot_count]
    tx_types = ["deposit", "withdraw", "transfer"]
    weights = [deposit_weight, withdraw_weight, transfer_weight]

    transactions: List[dict] = []
    current_ts = 0.0

    for tx_id in range(1, num_transactions + 1):
        tx_type = rng.choices(tx_types, weights=weights, k=1)[0]
        amount = round(rng.uniform(min_amount, max_amount), 2)

        # 20% of events happen almost immediately after a prior event.
        if rng.random() < 0.20:
            current_ts += rng.uniform(0.0005, 0.008)
        else:
            current_ts += rng.uniform(0.01, 0.30)

        if tx_type in ("deposit", "withdraw"):
            account = _pick_account(rng, accounts, hot_accounts)
            tx = {
                "id": tx_id,
                "type": tx_type,
                "account": account,
                "amount": amount,
                "ts": round(current_ts, 6),
            }
        else:
            src = _pick_account(rng, accounts, hot_accounts)
            dst = _pick_account(rng, accounts, hot_accounts)
            while dst == src:
                dst = _pick_account(rng, accounts, hot_accounts)
            tx = {
                "id": tx_id,
                "type": tx_type,
                "src": src,
                "dst": dst,
                "amount": amount,
                "ts": round(current_ts, 6),
            }

        transactions.append(tx)

    return transactions
