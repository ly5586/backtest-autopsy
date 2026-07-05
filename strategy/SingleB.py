"""SingleB — 24-line momentum strategy (MOM only) with trailing stop.

Stripped-down version of ADXMomentumFixed: removed redundant ADX and DI.
Recent backtest (2024-2026 OKX, 5m): 22,146 trades, 66.3% WR, +$5,635.
The trailing stop still inflates win rate. See SingleB_FixedRR for the truth.

WARNING: The win rate is still manufactured by the trailing stop.
See SingleB_FixedRR.py for the honest 1:1 version.
"""

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class SingleB(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True

    stoploss = -0.015
    trailing_stop = True
    trailing_only_offset_is_reached = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.01
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
