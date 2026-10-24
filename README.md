# Parallel Bank Transactions & Fraud Detection

A Python simulation of a bank transaction system that demonstrates race conditions under parallel execution (threads vs. processes) and then fixes them with synchronization (locks). It also includes fraud detection, performance comparison and plotting.

## Modules
- `transaction_generator.py` â€“ generates synthetic transactions
- `transaction_engine.py` â€“ core account and transfer logic
- `workers.py` / `runners.py` â€“ threaded and multiprocess execution
- `checker.py` â€“ verifies balance consistency and detects fraud patterns
- `performance.py` / `plotting.py` â€“ timing comparison and charts
- `main.py` â€“ runs the full pipeline

## Run
```bash
pip install -r requirements.txt
python main.py
```
On Windows you can also double-click `RUN_PROJECT.bat`. Charts are written to `outputs/`.

See `parallel_bank_project_spec.txt` for the full project specification.
