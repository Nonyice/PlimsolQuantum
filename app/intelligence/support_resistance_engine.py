from dataclasses import dataclass

from app.models.market_snapshot import MarketSnapshot


@dataclass(slots=True)
class PriceZone:

    timeframe: str

    zone_type: str

    lower: float

    upper: float

    center: float

    strength: float


@dataclass(slots=True)
class SupportResistanceAnalysis:

    supports: list

    resistances: list

    nearest_support: PriceZone | None

    nearest_resistance: PriceZone | None

    market_location: str


class SupportResistanceEngine:
    """
    Multi-Timeframe Support & Resistance Engine.

    Detects:

    • Swing Highs
    • Swing Lows
    • Support Zones
    • Resistance Zones
    • Nearest Levels
    """

    TIMEFRAME_WEIGHT = {

        "1m": 1,

        "5m": 2,

        "15m": 3,

        "1h": 5,

        "4h": 8,

        "1d": 13,

    }

    ZONE_PERCENT = 0.002

    def analyse(
        self,
        snapshot: MarketSnapshot,
    ):

        supports = []

        resistances = []

        current_price = None

        for tf, tf_data in snapshot.timeframes.items():

            candles = tf_data.candles

            closes = [
                float(c[4])
                for c in candles
            ]

            highs = [
                float(c[2])
                for c in candles
            ]

            lows = [
                float(c[3])
                for c in candles
            ]

            current_price = closes[-1]

            swing_high = max(highs[-50:])

            swing_low = min(lows[-50:])

            resistance = self._build_zone(

                timeframe=tf,

                zone_type="RESISTANCE",

                price=swing_high,

            )

            support = self._build_zone(

                timeframe=tf,

                zone_type="SUPPORT",

                price=swing_low,

            )

            supports.append(support)

            resistances.append(resistance)

        nearest_support = None

        nearest_resistance = None

        support_distance = float("inf")

        resistance_distance = float("inf")

        for zone in supports:

            if zone.center <= current_price:

                distance = current_price - zone.center

                if distance < support_distance:

                    support_distance = distance

                    nearest_support = zone

        for zone in resistances:

            if zone.center >= current_price:

                distance = zone.center - current_price

                if distance < resistance_distance:

                    resistance_distance = distance

                    nearest_resistance = zone

        location = "MIDDLE"

        if nearest_support:

            if current_price <= nearest_support.upper:

                location = "AT_SUPPORT"

        if nearest_resistance:

            if current_price >= nearest_resistance.lower:

                location = "AT_RESISTANCE"

        return SupportResistanceAnalysis(

            supports=supports,

            resistances=resistances,

            nearest_support=nearest_support,

            nearest_resistance=nearest_resistance,

            market_location=location,

        )

    def _build_zone(

        self,

        timeframe,

        zone_type,

        price,

    ):

        margin = price * self.ZONE_PERCENT

        weight = self.TIMEFRAME_WEIGHT.get(

            timeframe,

            1,

        )

        return PriceZone(

            timeframe=timeframe,

            zone_type=zone_type,

            lower=round(

                price - margin,

                8,

            ),

            upper=round(

                price + margin,

                8,

            ),

            center=round(

                price,

                8,

            ),

            strength=weight,

        )