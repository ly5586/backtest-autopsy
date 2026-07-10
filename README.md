# Backtest Autopsy

The strategy with the highest win rate lost money. The simplest strategy with the most boring exit made the most.

I spent two weeks testing trading strategies. Here's what I found.

---

## What I did

I tested 4 variations of a momentum-based strategy on OKX perpetual futures, 5-minute candles, 10 coins, from January 2024 to July 2026.

The original idea came from a public Freqtrade strategy called ADXMomentumFixed. It uses three indicators — ADX, +DI/-DI, and MOM — with a trailing stop. Looked professional. Felt legitimate.

Then I started peeling layers off.

---

## The results

| Strategy | Indicators | Exit type | Trades | Win rate | Profit |
|----------|:---:|------|------:|------:|------:|
| ADXMomentumFixed | ADX+DI+MOM | Trailing stop | 7,123 | 74.6% | **-$4,518** |
| ADXMomentumFixed_FixedRR | ADX+DI+MOM | Fixed 1:1 | 12,944 | 52.6% | +$2,040 |
| SingleB | MOM only | Trailing stop | 22,146 | 66.3% | +$5,635 |
| **SingleB_FixedRR** | **MOM only** | **Fixed 1:1** | **14,008** | **55.6%** | **+$8,814** |

Some things that surprised me:

- **The highest win rate strategy (74.6%) was the only one that lost money.** Its trailing stop was too tight — 0.1% offset on 5-minute candles basically means you exit at the first tick of noise before any trend can develop.

- **Fewer indicators made more money.** The 3-indicator version (ADXMomentumFixed) was the worst performer. Stripping it down to just MOM improved results across the board.

- **The fixed 1:1 exit beat the trailing stop in both comparisons.** I thought trailing stops were supposed to let winners run. In this market regime (a pretty strong bull run), they did the opposite — they cut winners short and let the commission stack up.

- **The simplest strategy won.** SingleB_FixedRR: one indicator, fixed stop and target, no leverage tricks. $8,814 profit. Not life-changing, but it was profitable across 14,000+ trades.

---

## Why the "professional" strategy failed

ADXMomentumFixed uses ADX to measure trend strength, +DI/-DI for directional pressure, and MOM for momentum. Three indicators, sounds thorough.

I ran a VIF (Variance Inflation Factor) test to check if they were actually independent:

| Indicator | VIF | Meaning |
|-----------|:---:|------|
| ADX(14) | 8.7 | Redundant |
| PLUS_DI(25) | 6.2 | Redundant |
| MINUS_DI(25) | 5.9 | Redundant |
| MOM(14) | 1.1 | Independent |

ADX and DI are literally calculated from the same directional movement formula. They can't be independent. Three indicators, one signal, and two of them were just adding noise.

The other problem was the trailing stop. ADXMomentumFixed uses a 0.1% trailing offset at 5x leverage. On a 5-minute candle, 0.1% is basically random price movement. The trailing stop was triggering on noise, not on actual reversals.

Here's what happens: price moves 0.3% in your direction → trailing stop activates at 0.2% → price hiccups 0.1% the other way → trailing stop fires, you're out at +0.1% → price then moves another 2% over the next 2 hours without you.

The strategy was built to "manage risk tightly" but it was actually just exiting every trade before it had room to work.

---

## What I think this means

I'm not saying these are universal truths. This is one experiment, one market regime (a crypto bull run), one timeframe. But here's what I took away:

1. **Test your indicators for collinearity before trusting them.** If two indicators share the same underlying formula (like ADX and DI both come from directional movement), they're not two independent signals. They're one signal with different wrappers.

2. **Test your entry signal with a fixed 1:1 exit first.** Before any trailing stop, any optimization, anything clever — just use a fixed 1.5% stop and 1.5% target. This tells you whether your entries have any edge at all. If win rate is below 50% with fixed exits, your entry signal isn't doing anything useful.

3. **More complexity makes things worse more often than it makes them better.** The 3-indicator strategy was the worst. The 1-indicator strategy was the best. This doesn't mean simple is always better — it means you should have to prove that each added indicator helps, not just assume it does.

4. **Win rate alone is meaningless.** The highest win rate lost money because the wins were tiny ($3 average) and the losses were huge ($27 average). You can have a 90% win rate and go broke if your risk/reward is bad enough.

5. **Trailing stops need room to breathe.** If your trailing offset is smaller than normal price noise on your timeframe, you're not managing risk. You're just exiting randomly.

6. **Backtesting isn't reality.** I ran SingleB in Freqtrade dry_run (live data, simulated fills) for 53 trades. 79% win rate, but -$91 actual PnL. The backtest numbers and the paper trading numbers told completely different stories.

---

## Limitations

- Only tested on crypto, only on OKX, only 5-minute timeframe, only 2024-2026 (which was a bull run)
- 4 strategies isn't a lot. I started with more but these were the only ones worth writing about
- Fees are included (OKX standard 0.05% taker) but real slippage might be higher
- The ADXMomentumFixed versions use 5x leverage, SingleB versions use 1x — so the absolute PnL numbers aren't directly comparable across families
- No buy-and-hold comparison. In this period, BTC alone went up ~300%. $8,814 on a $5,000 starting balance is about +176%, which is good but not amazing relative to the market

---

## How to run this yourself

If you already have Freqtrade set up:

```bash
git clone https://github.com/liu57liu456/backtest-autopsy.git
cd backtest-autopsy
pip install -r requirements.txt

# Download data
freqtrade download-data --config config.json --timerange 20240101- --timeframes 5m

# Run strategies
freqtrade backtesting --strategy ADXMomentumFixed --config config.json --timerange 20240101-
freqtrade backtesting --strategy ADXMomentumFixed_FixedRR --config config.json --timerange 20240101-
freqtrade backtesting --strategy SingleB --config config.json --timerange 20240101-
freqtrade backtesting --strategy SingleB_FixedRR --config config.json --timerange 20240101-

# Compare
python analysis/compare_strategies.py

# Charts
python analysis/generate_charts.py
```

If you don't want to set up Freqtrade, the `images/` folder has pre-generated charts from my backtest runs.

Don't put real API keys in config.json. The file uses placeholder values and dry_run mode.

---

## Files

```
├── README.md
├── strategy/
│   ├── ADXMomentumFixed.py           # 3-indicator + trailing stop
│   ├── ADXMomentumFixed_FixedRR.py   # 3-indicator + fixed 1:1
│   ├── SingleB.py                    # 1-indicator + trailing stop
│   └── SingleB_FixedRR.py            # 1-indicator + fixed 1:1
├── analysis/
│   ├── vif_analysis.py
│   ├── generate_charts.py
│   └── compare_strategies.py
├── images/
│   ├── comparison.png
│   └── equity_curves.png
├── config.json
├── requirements.txt
└── LICENSE
```

---

## License

MIT

---

Not financial advice. This is a postmortem of strategies that didn't work the way I expected. Backtest results don't guarantee anything about future performance. Trading involves risk of losing money.
