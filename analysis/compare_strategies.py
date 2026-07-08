"""Compare all 4 strategies from real Freqtrade backtest results.

Usage:
  1. Run backtests (from the project root):
     freqtrade backtesting --strategy ADXMomentumFixed --config config.json
     freqtrade backtesting --strategy ADXMomentumFixed_FixedRR --config config.json
     freqtrade backtesting --strategy SingleB --config config.json
     freqtrade backtesting --strategy SingleB_FixedRR --config config.json

  2. Run this script:
     python analysis/compare_strategies.py

If you don't want to run backtests, see images/comparison.png for pre-computed results.
"""

import json
import os
import sys
import zipfile
from pathlib import Path

FREQTRADE_DIR = Path(os.environ.get(
    "FREQTRADE_DIR",
    Path.home() / "OneDrive" / "Desktop" / "freqtrade",
))
RESULTS_DIR = FREQTRADE_DIR / "user_data" / "backtest_results"


def load_results(strategy_name: str) -> dict | None:
    """Find the latest backtest result for a given strategy.

    Handles both .json and .zip backtest output formats.
    """
    if not RESULTS_DIR.is_dir():
        return None

    # Check both .json and .zip files, newest first
    entries = sorted(
        [e for e in os.listdir(RESULTS_DIR)
         if e.endswith(".json") or e.endswith(".zip")],
        key=lambda e: os.path.getmtime(RESULTS_DIR / e),
        reverse=True,
    )

    for fname in entries:
        path = RESULTS_DIR / fname
        try:
            if fname.endswith(".zip"):
                data = _read_zip(path)
            else:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
        except (json.JSONDecodeError, zipfile.BadZipFile, OSError):
            continue

        if data is None:
            continue

        results = data.get("strategy_comparison", [])
        for r in results:
            if r.get("key") == strategy_name:
                return {
                    "strategy": strategy_name,
                    "trades": r.get("total_trades", 0),
                    "win_rate": r.get("win_rate", 0) * 100,
                    "profit_abs": r.get("profit_total_abs", 0),
                    "profit_pct": r.get("profit_total_pct", 0) * 100,
                    "drawdown": r.get("max_drawdown_account", 0) * 100,
                    "avg_duration": r.get("avg_duration", "?"),
                    "file": fname,
                }
    return None


def _read_zip(path: Path) -> dict | None:
    """Read the first non-config JSON from a backtest zip."""
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if name.endswith(".json") and "config" not in name.lower():
                return json.loads(zf.read(name))
    return None


def main():
    strategies = [
        "ADXMomentumFixed",
        "ADXMomentumFixed_FixedRR",
        "SingleB",
        "SingleB_FixedRR",
    ]

    results = {}
    for s in strategies:
        r = load_results(s)
        if r:
            results[s] = r

    if not results:
        print("No backtest results found.")
        print(f"Expected directory: {RESULTS_DIR}")
        print("\nRun backtests first (from project root):")
        for s in strategies:
            print(f"  freqtrade backtesting --strategy {s} --config config.json")
        print("\nOr see images/comparison.png for pre-computed results.")
        sys.exit(1)

    print("\n" + "=" * 75)
    print("  Strategy Comparison — Trailing Stop vs Fixed 1:1")
    print("=" * 75)
    print()

    header = (f"{'Strategy':<28} {'Exit':<15} {'Trades':>8} "
              f"{'Win%':>8} {'Profit':>12} {'DD%':>8}")
    print(header)
    print("-" * 75)

    order = [
        ("ADXMomentumFixed", "Trailing Stop"),
        ("ADXMomentumFixed_FixedRR", "Fixed 1:1"),
        ("SingleB", "Trailing Stop"),
        ("SingleB_FixedRR", "Fixed 1:1"),
    ]

    for name, exit_type in order:
        r = results.get(name)
        if r:
            print(f"  {name:<26}  {exit_type:<13}  {r['trades']:>6}  "
                  f"{r['win_rate']:>5.1f}%  ${r['profit_abs']:>10,.0f}  "
                  f"{r['drawdown']:>5.1f}%")
        else:
            print(f"  {name:<26}  {exit_type:<13}  {'N/A':>6}  "
                  f"{'N/A':>5}   {'N/A':>10}  {'N/A':>5}")

    print("-" * 75)

    # Find the winner and loser
    if results:
        best = max(results.values(), key=lambda r: r["profit_abs"])
        worst = min(results.values(), key=lambda r: r["profit_abs"])
        print(f"\n  Best:  {best['strategy']} — {best['win_rate']:.1f}% WR, "
              f"${best['profit_abs']:+,.0f}")
        print(f"  Worst: {worst['strategy']} — {worst['win_rate']:.1f}% WR, "
              f"${worst['profit_abs']:+,.0f}")

        if worst["win_rate"] > best["win_rate"]:
            print("\n  ★ The highest win rate strategy was the least profitable.")
            print("    Win rate is not profit. Exit logic matters more than entry.")

    print()


if __name__ == "__main__":
    main()
