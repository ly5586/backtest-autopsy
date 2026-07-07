"""ADXMomentumFixed — 3-indicator strategy with tight trailing stop.

ADX(14) + DI(25) + MOM(14) entry signals.
Recent backtest (2024-2026 OKX, 5m): 7,123 trades, 74.6% WR, -$4,518.
The tight trailing stop (0.1%) systematically cuts winners early.
See ADXMomentumFixed_FixedRR for the honest fixed 1:1 version.

WARNING: VIF analysis reveals all 3 indicators are collinear.
ADX is a NEGATIVE contributor. See README for full analysis.
"""

from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class ADXMomentumFixed(IStrategy):
    INTERFACE_VERSION = 3
    can_short = True

    # --- Exit rules ---
    stoploss = -0.05                         # 5% hard stop (rarely hit)
    trailing_stop = True                     # <-- THIS is what makes the 93.7%
    trailing_stop_positive = 0.001           # 0.1% trail
    trailing_stop_positive_offset = 0.005    # 0.5% activation
    trailing_only_offset_is_reached = True
    minimal_roi = {"0": 0.015}              # 1.5% take-profit floor

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
