from dataclasses import dataclass

import numpy as np
import talib


@dataclass(slots=True)
class IndicatorSet:

    ema20: float

    ema50: float

    ema200: float

    rsi: float

    atr: float

    adx: float

    macd: float

    macd_signal: float

    macd_histogram: float

    upper_bb: float

    middle_bb: float

    lower_bb: float


class IndicatorService:

    def calculate(self, candles):

        highs = np.array(

            [float(c[2]) for c in candles],

            dtype=float,

        )

        lows = np.array(

            [float(c[3]) for c in candles],

            dtype=float,

        )

        closes = np.array(

            [float(c[4]) for c in candles],

            dtype=float,

        )

        ema20 = talib.EMA(closes, timeperiod=20)

        ema50 = talib.EMA(closes, timeperiod=50)

        ema200 = talib.EMA(closes, timeperiod=200)

        rsi = talib.RSI(closes)

        atr = talib.ATR(

            highs,

            lows,

            closes,

            timeperiod=14,

        )

        adx = talib.ADX(

            highs,

            lows,

            closes,

            timeperiod=14,

        )

        macd, signal, hist = talib.MACD(closes)

        upper, middle, lower = talib.BBANDS(closes)

        return IndicatorSet(

            ema20=float(ema20[-1]),

            ema50=float(ema50[-1]),

            ema200=float(ema200[-1]),

            rsi=float(rsi[-1]),

            atr=float(atr[-1]),

            adx=float(adx[-1]),

            macd=float(macd[-1]),

            macd_signal=float(signal[-1]),

            macd_histogram=float(hist[-1]),

            upper_bb=float(upper[-1]),

            middle_bb=float(middle[-1]),

            lower_bb=float(lower[-1]),

        )