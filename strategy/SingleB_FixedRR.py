"""SingleB_FixedRR — MOM-only entry, honest 1:1 risk/reward exit.

Same entry as SingleB, but with fixed 1.5% stop-loss and 1.5% take-profit.
Recent backtest (2024-2026 OKX, 5m): 14,008 trades, 55.6% WR, +$8,814.
This is the best performer — the simplest strategy with the most honest exit.
"""

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class SingleB_FixedRR(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True

    stoploss = -0.015
    trailing_stop = False
    minimal_roi = {"0": 0.015}
    timeframe = "5m"
    process_only_new_candles = True
    use_exit_signal = False
    startup_candle_count = 50

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        df['mom'] = ta.MOM(df, timeperiod=14)
        df["hour"] = df["date"].dt.hour
        df["weekday"] = df["date"].dt.dayofweek
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        active = (df["hour"] >= 6) & (df["hour"] <= 23) & (df["weekday"] < 5)
        df.loc[active & (df['mom'] > 0), 'enter_long'] = 1
        df.loc[active & (df['mom'] < 0), 'enter_short'] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        return df
