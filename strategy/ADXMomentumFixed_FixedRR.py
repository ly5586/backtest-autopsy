"""ADXMomentumFixed_FixedRR — Same 3-indicator entry, honest 1:1 exit.

Replaces the trailing stop with fixed 1.5% stop-loss and 1.5% take-profit.
Exposes the true accuracy of the ADX+DI+MOM entry signal.
"""

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class ADXMomentumFixed_FixedRR(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True

    # --- Fixed 1:1 exit (no trailing manipulation) ---
    stoploss = -0.015
    trailing_stop = False
    minimal_roi = {"0": 0.015}

    timeframe = "5m"
    process_only_new_candles = True
    use_exit_signal = False
    startup_candle_count = 50

    def populate_indicators(self, df: DataFrame, metadata: dict) -> DataFrame:
        df['adx'] = ta.ADX(df, timeperiod=14)
        df['plus_di'] = ta.PLUS_DI(df, timeperiod=25)
        df['minus_di'] = ta.MINUS_DI(df, timeperiod=25)
        df['mom'] = ta.MOM(df, timeperiod=14)
        df["hour"] = df["date"].dt.hour
        df["weekday"] = df["date"].dt.dayofweek
        return df

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        active = (df["hour"] >= 6) & (df["hour"] <= 23) & (df["weekday"] < 5)
        trend = df['adx'] > 25
        df.loc[active & trend & (df['mom'] > 0) & (df['plus_di'] > 25)
               & (df['plus_di'] > df['minus_di']), 'enter_long'] = 1
        df.loc[active & trend & (df['mom'] < 0) & (df['minus_di'] > 25)
               & (df['minus_di'] > df['plus_di']), 'enter_short'] = 1
        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        return df

    def leverage(self, pair, current_time, current_rate,
                 proposed_leverage, max_leverage, entry_tag, side, **kwargs) -> float:
        return 5.0
