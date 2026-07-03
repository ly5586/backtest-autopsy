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

All strategies start with $5,000. Backtest period: January 2024 – July 2026, OKX perpetual futures, 5-minute candles, 10 coins. For reference, Bitcoin went from $42,298 to $61,950 in this period — a 46.5% gain. Buying and holding BTC would have turned $5,000 into $7,323.

| Strategy | Indicators | Exit type | Leverage | Trades | Win rate | Profit |
|----------|:---:|------|:---:|------:|------:|------:|
| ADXMomentumFixed | ADX+DI+MOM | Trailing stop | 5× | 7,123 | 74.6% | **-$4,518** |
| ADXMomentumFixed_FixedRR | ADX+DI+MOM | Fixed 1:1 | 5× | 1,292 | 36.9% | **-$4,495** |
| SingleB | MOM only | Trailing stop | 1× | 22,146 | 66.3% | +$5,635 |
| **SingleB_FixedRR** | **MOM only** | **Fixed 1:1** | **1×** | **14,008** | **55.6%** | **+$8,814** |
| *BTC buy-and-hold* | *—* | *—* | *—* | *—* | *—* | *+$2,323* |

Some things that surprised me:

- **The trailing stop inflated ADXMomentumFixed's win rate from 36.9% to 74.6%.** That's not an edge — that's a 38 percentage point artifact. With the same entries and a fixed 1:1 exit, the true accuracy is worse than a coin flip. The trailing stop converts losers into "small wins" by exiting at the first micro-bounce before the stop loss is hit, then counts them as wins in the stats. At 5× leverage, this effect is amplified because small price moves equal large PnL swings.

- **At 5× leverage, both ADXMomentumFixed variants lost nearly everything.** The trailing version lost 90% of the account. The fixed version lost 90% of the account. The entry signal simply has no edge at this timeframe and distance, and leverage magnifies the noise.

- **Fewer indicators did better.** The 3-indicator version was the worst. SingleB (MOM only) improved results. But it's worth noting: the ADX versions used 5× leverage and SingleB used 1×, so the comparison across families isn't apples-to-apples on PnL. The levered versions got destroyed; the unlevered versions survived.

- **Fixed 1:1 beat trailing in both families.** ADXMomentumFixed_FixedRR (-$4,495) was marginally less bad than ADXMomentumFixed (-$4,518), and SingleB_FixedRR (+$8,814) beat SingleB (+$5,635). The trailing stop was cutting winners short, not protecting profits.

- **BTC buy-and-hold returned +46.5%.** SingleB_FixedRR's +176% beat it, but the gap is smaller than it looks when you account for the 14,008 trades' worth of fees and the concentration risk of being in 10 altcoins vs one Bitcoin.

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

2. **Test your entry signal with a fixed 1:1 exit first.** Before any trailing stop, any optimization, anything clever — just use a fixed 1.5% stop and 1.5% target. ADXMomentumFixed's true accuracy went from 74.6% to 36.9% when I did this. A 36.9% win rate with 1:1 risk/reward is a negative-expectancy game — you lose 1.5% 63% of the time and gain 1.5% 37% of the time. The math doesn't work, and no exit optimization can fix an entry signal that's worse than random.

3. **More complexity makes things worse more often than it makes them better.** The 3-indicator strategy was the worst. The 1-indicator strategy was the best. This doesn't mean simple is always better — it means you should have to prove that each added indicator helps, not just assume it does.

4. **Win rate alone is meaningless, especially with leverage.** ADXMomentumFixed showed 74.6% WR but lost 90% of the account. At 5× leverage, the trailing stop's micro-wins ($3 average) couldn't offset the occasional full-stop-loss disaster ($27 average). You can have a high win rate and still get wiped out.

5. **Trailing stops need room to breathe.** If your trailing offset is smaller than normal price noise on your timeframe, you're not managing risk. You're just exiting randomly.

6. **Backtesting isn't reality.** I ran SingleB in Freqtrade dry_run (live data, simulated fills) for 53 trades. 79% win rate, but -$91 actual PnL. The backtest numbers and the paper trading numbers told completely different stories.

---

## Limitations

- Only tested on crypto, only on OKX, only 5-minute timeframe, only January 2024 – July 2026 (which included a strong bull run — BTC went from $42K to $62K, +46.5%)
- 4 strategies isn't a lot. I started with more but these were the only ones worth writing about
- Fees are included (OKX standard 0.05% taker) but real slippage might be higher
- ADXMomentumFixed uses 5× leverage; SingleB uses 1× leverage. The ADX versions' extreme losses are partly a leverage story, not just an exit-logic story. A fair comparison across families would require running all four strategies at both leverage levels
- BTC buy-and-hold is now included as a baseline. But BTC ≠ a basket of 10 altcoins — the risk profiles are completely different

---

## How to run this yourself

If you already have Freqtrade set up:

```bash
git clone https://github.com/ly5586/backtest-autopsy.git
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

---

*Last updated: 2026-07-11*
