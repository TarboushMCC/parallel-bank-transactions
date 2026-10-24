"""Correctness checks for execution results."""

from __future__ import annotations

from typing import Dict, Tuple


def find_negative_balances(balances: Dict[int, float]) -> Dict[int, float]:
    return {account: bal for account, bal in balances.items() if bal < 0.0}


def compare_balances(
    baseline_balances: Dict[int, float],
    candidate_balances: Dict[int, float],
    tolerance: float = 1e-6,
) -> Tuple[int, float]:
    mismatched = 0
    total_abs_error = 0.0

    for account, baseline in baseline_balances.items():
        observed = float(candidate_balances.get(account, 0.0))
        diff = abs(float(baseline) - observed)
        if diff > tolerance:
            mismatched += 1
            total_abs_error += diff

    return mismatched, total_abs_error


def build_correctness_report(
    baseline_balances: Dict[int, float],
    candidate_balances: Dict[int, float],
) -> Dict[str, float]:
    negatives = find_negative_balances(candidate_balances)
    mismatched, total_abs_error = compare_balances(baseline_balances, candidate_balances)

    return {
        "negative_accounts": len(negatives),
        "mismatched_accounts": mismatched,
        "total_abs_error": total_abs_error,
        "matches_serial": 1 if mismatched == 0 else 0,
        "no_negative_balances": 1 if len(negatives) == 0 else 0,
    }
