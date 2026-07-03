"""Generate charts from real Freqtrade backtest results.

Reads the latest backtest JSON output and renders comparison charts.
Falls back to known real results if no backtest data is found.
"""

import json
import os
import sys
import zipfile
import glob
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# --- Output ---
OUT = Path(__file__).resolve().parent.parent / "images"
OUT.mkdir(exist_ok=True)

# --- GitHub-dark style ---
STYLE = {
    "figure.facecolor": "#0d1117",
    "axes.facecolor": "#0d1117",
    "axes.edgecolor": "#30363d",
    "axes.labelcolor": "#c9d1d9",
    "text.color": "#c9d1d9",
    "xtick.color": "#8b949e",
    "ytick.color": "#8b949e",
    "grid.color": "#21262d",
    "grid.alpha": 0.4,
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
}
plt.rcParams.update(STYLE)

# --- Real backtest results (2024-2026, 5m, OKX futures) ---
REAL_RESULTS = {
    "ADXMomentumFixed": {
        "label": "3 Indicators\n+ Trailing (5×)",
        "trades": 7123,
        "win_rate": 74.6,
        "profit": -4518,
        "color": "#58a6ff",
        "group": "Complex",
    },
    "ADXMomentumFixed_FixedRR": {
        "label": "3 Indicators\n+ Fixed 1:1 (5×)",
        "trades": 1292,
        "win_rate": 36.9,
        "profit": -4495,
        "color": "#f0883e",
        "group": "Complex",
    },
    "SingleB": {
        "label": "1 Indicator\n+ Trailing (1×)",
        "trades": 22146,
        "win_rate": 66.3,
        "profit": 5635,
        "color": "#3fb950",
        "group": "Simple",
    },
    "SingleB_FixedRR": {
        "label": "1 Indicator\n+ Fixed 1:1 (1×)",
        "trades": 14008,
        "win_rate": 55.6,
        "profit": 8814,
        "color": "#d2a8ff",
        "group": "Simple",
    },
}


def try_load_from_backtest() -> dict | None:
    """Try to enrich results with equity curves from backtest zip files."""
    results_dir = Path.home() / "OneDrive" / "Desktop" / "freqtrade" / "user_data" / "backtest_results"
    if not results_dir.is_dir():
        return None

    loaded = {}
    zips = sorted(glob.glob(str(results_dir / "backtest-result-*.zip")),
                  key=os.path.getmtime, reverse=True)

    for zpath in zips:
        try:
            with zipfile.ZipFile(zpath) as zf:
                for name in zf.namelist():
                    if name.endswith(".json") and "config" not in name:
                        data = json.loads(zf.read(name))
                        for strat_name, strat_data in data.get("strategy", {}).items():
                            if strat_name not in loaded:
                                trades = strat_data.get("trades", [])
                                equity = []
                                balance = 5000
                                for t in trades:
                                    balance += t.get("profit_abs", 0)
                                    equity.append(balance)
                                loaded[strat_name] = {
                                    "equity": equity,
                                    "trades": len(trades),
                                }
        except Exception:
            continue

    return loaded if loaded else None


def plot_main_comparison(results: dict, filepath: Path):
    """4-strategy comparison: win rate vs profit."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Backtest Autopsy — Strategy Comparison",
                 fontweight="bold", fontsize=18, y=0.98)

    order = ["ADXMomentumFixed", "ADXMomentumFixed_FixedRR",
             "SingleB", "SingleB_FixedRR"]

    # --- Top-left: Win Rate ---
    ax = axes[0][0]
    labels = [results[k]["label"] for k in order]
    wrs = [results[k]["win_rate"] for k in order]
    colors = [results[k]["color"] for k in order]
    bars = ax.bar(range(len(labels)), wrs, color=colors, width=0.55, edgecolor="none")

    ax.axhline(y=50, color="#8b949e", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.text(3.3, 51, "Coin flip (50%)", fontsize=9, color="#8b949e", va="bottom")

    for bar, wr in zip(bars, wrs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{wr:.1f}%", ha="center", fontsize=13, fontweight="bold",
                color="#c9d1d9")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("Win Rate", fontweight="bold", fontsize=14, color="#c9d1d9")
    ax.set_ylim(0, max(wrs) * 1.15)
    ax.grid(True, linestyle="--", linewidth=0.3, axis="y")

    # --- Top-right: Net Profit ---
    ax = axes[0][1]
    profits = [results[k]["profit"] for k in order]
    profit_colors = ["#f85149" if p < 0 else "#3fb950" for p in profits]
    bars = ax.bar(range(len(labels)), profits, color=profit_colors, width=0.55, edgecolor="none")
    ax.axhline(y=0, color="#8b949e", linewidth=0.8)

    for bar, p in zip(bars, profits):
        sign = "+" if p >= 0 else "-"
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + (max(abs(min(profits)), max(profits)) * 0.05) * (1 if p >= 0 else -1),
                f"{sign}${abs(p):,}", ha="center", fontsize=12, fontweight="bold",
                color="#3fb950" if p >= 0 else "#f85149")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("Net Profit (USDT)", fontweight="bold", fontsize=14, color="#c9d1d9")
    ax.grid(True, linestyle="--", linewidth=0.3, axis="y")

    # --- Bottom-left: Trade Count ---
    ax = axes[1][0]
    trades = [results[k]["trades"] for k in order]
    bars = ax.bar(range(len(labels)), trades, color=colors, width=0.55, edgecolor="none")
    for bar, t in zip(bars, trades):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(trades) * 0.02,
                f"{t:,}", ha="center", fontsize=12, fontweight="bold", color="#c9d1d9")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("Total Trades", fontweight="bold", fontsize=14, color="#c9d1d9")
    ax.grid(True, linestyle="--", linewidth=0.3, axis="y")

    # --- Bottom-right: Scatter: Win Rate vs Profit ---
    ax = axes[1][1]
    for key in order:
        r = results[key]
        ax.scatter(r["win_rate"], r["profit"], s=r["trades"] / 50,
                   c=r["color"], alpha=0.85, edgecolors="white", linewidth=0.5,
                   zorder=3)
        offset_x = 1.2 if key == "ADXMomentumFixed" else -1.5 if key == "SingleB_FixedRR" else 1.0
        offset_y = 400 if "Fixed" in key else -400
        ax.annotate(r["label"].replace("\n", " "), (r["win_rate"], r["profit"]),
                    textcoords="offset points", xytext=(offset_x * 5, offset_y / 50),
                    fontsize=8, color="#8b949e", ha="center")

    ax.axhline(y=0, color="#8b949e", linewidth=0.8)
    ax.axvline(x=50, color="#8b949e", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.set_xlabel("Win Rate (%)", fontsize=11)
    ax.set_ylabel("Net Profit (USDT)", fontsize=11)
    ax.set_title("Win Rate vs Profit (bubble = trade count)", fontweight="bold",
                 fontsize=14, color="#c9d1d9")
    ax.grid(True, linestyle="--", linewidth=0.3)

    # Annotate quadrants
    ax.text(47, max(profits) * 0.85, "LOW win rate\nHIGH profit",
            fontsize=9, color="#3fb950", ha="right", alpha=0.7)
    ax.text(72, min(profits) * 0.5, "HIGH win rate\nLOW profit",
            fontsize=9, color="#f85149", ha="left", alpha=0.7)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(filepath, dpi=150, facecolor=fig.get_facecolor(),
                edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {filepath}")


def plot_equity_curves(backtest_data: dict, filepath: Path):
    """Plot real equity curves from backtest trade data."""
    if not backtest_data:
        print("  Skipping equity curves (no backtest data loaded)")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    colors = {"ADXMomentumFixed": "#58a6ff", "SingleB": "#3fb950",
              "ADXMomentumFixed_FixedRR": "#f0883e", "SingleB_FixedRR": "#d2a8ff"}

    for strat_name, strat_data in backtest_data.items():
        equity = strat_data.get("equity", [])
        if not equity:
            continue
        color = colors.get(strat_name, "#8b949e")
        x = np.arange(len(equity))
        ax.plot(x, equity, linewidth=0.8, color=color, alpha=0.9,
                label=f"{strat_name} ({len(equity)} trades)")

    ax.axhline(y=5000, color="#8b949e", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.text(0, 5050, "Initial: $5,000", fontsize=9, color="#8b949e")
    ax.set_xlabel("Trade Number")
    ax.set_ylabel("Equity (USDT)")
    ax.set_title("Real Equity Curves — 2024-2026 OKX Futures",
                 fontweight="bold", fontsize=14)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, linestyle="--", linewidth=0.3)

    fig.tight_layout()
    fig.savefig(filepath, dpi=150, facecolor=fig.get_facecolor(),
                edgecolor="none")
    plt.close(fig)
    print(f"  Saved: {filepath}")


def main():
    print("Generating charts from real backtest data...")

    # Try to load detailed trade data for equity curves
    backtest_data = try_load_from_backtest()
    if backtest_data:
        print(f"  Loaded detailed data for {len(backtest_data)} strategies")
    else:
        print("  No detailed backtest data found, using summary stats only")

    # Main comparison (always works with REAL_RESULTS)
    plot_main_comparison(REAL_RESULTS, OUT / "comparison.png")

    # Equity curves (only if we have detailed data)
    if backtest_data:
        plot_equity_curves(backtest_data, OUT / "equity_curves.png")

    print(f"\nDone. Charts saved to {OUT}/")
    for f in sorted(OUT.glob("*.png")):
        print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
