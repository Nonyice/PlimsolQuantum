from dataclasses import dataclass


@dataclass(slots=True)
class Opportunity:
    score: float
    grade: str
    probability: float
    tradable: bool
    reason: str
    expected_reward: float
    expected_risk: float
    direction: str


class OpportunityEngine:
    """
    Converts market evidence into a directional opportunity.

    IMPORTANT:
    Confidence is the primary PQI execution signal.

    The OpportunityEngine calculates:
        - quality score
        - confidence/probability
        - direction
        - move quality
        - reversal risk

    The final DecisionEngine decides whether the confidence is sufficient
    to execute.

    ``tradable`` is retained for compatibility and reporting, but it is
    deliberately NOT used as the final execution gate.
    """

    TREND_WEIGHT = 30
    MOMENTUM_WEIGHT = 25
    VOLUME_WEIGHT = 10
    VOLATILITY_WEIGHT = 10
    SUPPORT_WEIGHT = 10
    PERSONALITY_WEIGHT = 15

    MIN_SCORE = 54
    MIN_1H_ADX = 16
    MIN_1H_STRENGTH = 0.25

    def evaluate(
        self,
        trend,
        momentum,
        volume,
        volatility,
        support,
        personality,
        anchor_timeframe="1h",
        snapshot=None,
    ):
        score = 0.0

        # ------------------------------------------------------------
        # Anchor trend
        # ------------------------------------------------------------

        anchor = trend.trends.get(anchor_timeframe)

        alignment = max(
            0.0,
            min(
                1.0,
                float(trend.alignment_score or 0),
            ),
        )

        anchor_quality = 0.0

        if anchor is not None:

            adx = float(anchor.adx or 0)

            adx_quality = max(
                0.0,
                min(
                    1.0,
                    (adx - self.MIN_1H_ADX) / 22.0,
                ),
            )

            strength_quality = max(
                0.0,
                min(
                    1.0,
                    float(anchor.strength or 0),
                ),
            )

            ema_quality = 1.0 if (
                (
                    anchor.direction == "BULLISH"
                    and anchor.ema20 > anchor.ema50 > anchor.ema200
                )
                or
                (
                    anchor.direction == "BEARISH"
                    and anchor.ema20 < anchor.ema50 < anchor.ema200
                )
            ) else 0.5

            anchor_quality = (
                (adx_quality * 0.45)
                + (strength_quality * 0.35)
                + (ema_quality * 0.20)
            )

        trend_quality = (
            (alignment * 0.60)
            + (anchor_quality * 0.40)
        )

        score += trend_quality * self.TREND_WEIGHT

        score += (
            momentum.confidence / 100.0
        ) * self.MOMENTUM_WEIGHT

        # ------------------------------------------------------------
        # Volume
        # ------------------------------------------------------------

        if volume.confirmed:

            score += self.VOLUME_WEIGHT

        elif volume.confidence >= 50:

            score += self.VOLUME_WEIGHT * 0.50

        else:

            score += self.VOLUME_WEIGHT * 0.25

        # ------------------------------------------------------------
        # Volatility
        # ------------------------------------------------------------

        if volatility.overall_regime == "NORMAL":

            score += self.VOLATILITY_WEIGHT

        elif volatility.overall_regime == "LOW":

            score += self.VOLATILITY_WEIGHT * 0.70

        elif (
            volatility.overall_regime == "HIGH"
            and volatility.explosive
        ):

            score += self.VOLATILITY_WEIGHT * 0.70

        else:

            score += self.VOLATILITY_WEIGHT * 0.35

        # ------------------------------------------------------------
        # Support / resistance
        # ------------------------------------------------------------

        if support.market_location == "AT_SUPPORT":

            score += self.SUPPORT_WEIGHT

        elif support.market_location == "AT_RESISTANCE":

            score += self.SUPPORT_WEIGHT * 0.80

        else:

            score += self.SUPPORT_WEIGHT * 0.45

        # ------------------------------------------------------------
        # Personality contributes to score only.
        #
        # It does NOT become an execution gate.
        # ------------------------------------------------------------

        if personality.tradable:

            score += (
                personality.confidence / 100.0
            ) * self.PERSONALITY_WEIGHT

        else:

            score += (
                personality.confidence / 100.0
            ) * (
                self.PERSONALITY_WEIGHT * 0.45
            )

        # ------------------------------------------------------------
        # Direction
        # ------------------------------------------------------------

        anchor_direction = "SIDEWAYS"
        anchor_adx = 0.0
        anchor_strength = 0.0

        if anchor is not None:

            anchor_direction = anchor.direction

            anchor_adx = float(
                anchor.adx or 0
            )

            anchor_strength = float(
                anchor.strength or 0
            )

        # ------------------------------------------------------------
        # Directional confidence
        # ------------------------------------------------------------

        direction_confidence = self._direction_confidence(
            trend,
            momentum,
            volume,
            anchor,
            anchor_direction,
        )

        # ------------------------------------------------------------
        # Move context
        # ------------------------------------------------------------

        move_capture, reversal_risk = self._move_context(
            snapshot,
            anchor_direction,
        )

        # ------------------------------------------------------------
        # Final confidence
        # ------------------------------------------------------------

        confidence = round(
            (direction_confidence * 0.50)
            + (move_capture * 0.25)
            + ((100.0 - reversal_risk) * 0.25),
            2,
        )

        # ------------------------------------------------------------
        # Fast direction
        # ------------------------------------------------------------

        fast_direction = None
        fast_votes = []

        if snapshot is not None:

            for tf in (
                "1m",
                "5m",
                "15m",
            ):

                tf_data = snapshot.timeframes.get(tf)

                if not tf_data:
                    continue

                if len(tf_data.candles) < 4:
                    continue

                closes = [
                    float(c[4])
                    for c in tf_data.candles
                ]

                base = closes[-4]

                move = (
                    ((closes[-1] - base) / base) * 100.0
                    if base
                    else 0.0
                )

                if abs(move) >= 0.10:

                    fast_votes.append(
                        "BULLISH"
                        if move > 0
                        else "BEARISH"
                    )

        if fast_votes:

            bullish_votes = fast_votes.count(
                "BULLISH"
            )

            bearish_votes = fast_votes.count(
                "BEARISH"
            )

            if bullish_votes > bearish_votes:

                fast_direction = "BULLISH"

            elif bearish_votes > bullish_votes:

                fast_direction = "BEARISH"

        # ------------------------------------------------------------
        # Legacy tradable state.
        #
        # This is now informational. It does NOT control execution.
        # ------------------------------------------------------------

        fast_trigger = (
            fast_direction in {
                "BULLISH",
                "BEARISH",
            }
            and fast_direction == anchor_direction
            and move_capture >= 45
            and confidence >= 55
            and reversal_risk < 78
            and not momentum.exhaustion
        )

        anchor_ok = (
            anchor_direction in {
                "BULLISH",
                "BEARISH",
            }
            and anchor_adx >= self.MIN_1H_ADX
            and anchor_strength >= self.MIN_1H_STRENGTH
        )

        tradable = (
            (
                anchor_ok
                and score >= self.MIN_SCORE
                and confidence >= 58
            )
            or fast_trigger
        )

        # Keep this informational condition from becoming an execution
        # blocker. Confidence is handled by DecisionEngine.
        if (
            reversal_risk >= 78
            or (
                volatility.overall_regime == "HIGH"
                and not volume.confirmed
                and not fast_trigger
            )
        ):
            tradable = False

        score = round(
            min(score, 100.0),
            2,
        )

        probability = confidence

        # ------------------------------------------------------------
        # Grade
        # ------------------------------------------------------------

        if score >= 90:

            grade = "A+"

        elif score >= 80:

            grade = "A"

        elif score >= 70:

            grade = "B"

        elif score >= 60:

            grade = "C"

        else:

            grade = "REJECT"

        # ------------------------------------------------------------
        # Reason
        # ------------------------------------------------------------

        if anchor_direction in {
            "BULLISH",
            "BEARISH",
        }:

            reason = (
                f"{grade} "
                f"{anchor_direction.lower()} setup: "
                f"confidence {confidence:.1f}, "
                f"move quality {move_capture:.1f}, "
                f"reversal risk {reversal_risk:.1f}."
            )

        else:

            reason = (
                f"No clear directional trend. "
                f"Confidence {confidence:.1f}."
            )

        expected_reward = round(
            1.5 + (score / 25),
            2,
        )

        expected_risk = round(
            max(
                1,
                6 - expected_reward,
            ),
            2,
        )

        return Opportunity(
            score=score,
            grade=grade,
            probability=probability,
            tradable=tradable,
            reason=reason,
            expected_reward=expected_reward,
            expected_risk=expected_risk,
            direction=anchor_direction,
        )

    # ================================================================
    # DIRECTION CONFIDENCE
    # ================================================================

    @staticmethod
    def _direction_confidence(
        trend,
        momentum,
        volume,
        anchor,
        direction,
    ):

        if direction not in {
            "BULLISH",
            "BEARISH",
        }:

            return 50.0

        alignment = max(
            0.0,
            min(
                1.0,
                float(
                    trend.alignment_score or 0
                ),
            ),
        )

        momentum_quality = max(
            0.0,
            min(
                1.0,
                float(
                    momentum.confidence or 0
                ) / 100.0,
            ),
        )

        volume_quality = max(
            0.0,
            min(
                1.0,
                float(
                    volume.confidence or 0
                ) / 100.0,
            ),
        )

        anchor_quality = 0.0

        if anchor is not None:

            adx_quality = max(
                0.0,
                min(
                    1.0,
                    (
                        float(anchor.adx or 0)
                        - 18.0
                    ) / 22.0,
                ),
            )

            strength_quality = max(
                0.0,
                min(
                    1.0,
                    float(
                        anchor.strength or 0
                    ),
                ),
            )

            anchor_quality = (
                (adx_quality * 0.55)
                + (strength_quality * 0.45)
            )

        return round(
            100.0 * (
                alignment * 0.35
                + anchor_quality * 0.30
                + momentum_quality * 0.25
                + volume_quality * 0.10
            ),
            2,
        )

    # ================================================================
    # MOVE / REVERSAL CONTEXT
    # ================================================================

    def _move_context(
        self,
        snapshot,
        direction,
    ):

        if (
            snapshot is None
            or direction not in {
                "BULLISH",
                "BEARISH",
            }
        ):

            return 50.0, 35.0

        move_scores = []
        reversal_scores = []
        direction_votes = []

        for tf, lookback in (
            ("1m", 5),
            ("5m", 3),
            ("15m", 2),
        ):

            tf_data = snapshot.timeframes.get(tf)

            if not tf_data:
                continue

            if len(tf_data.candles) < (
                lookback + 1
            ):
                continue

            candles = tf_data.candles

            closes = [
                float(c[4])
                for c in candles
            ]

            opens = [
                float(c[1])
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

            start = closes[
                -(lookback + 1)
            ]

            last = closes[-1]

            if start <= 0:
                continue

            signed_return = (
                (last - start)
                / start
            ) * 100.0

            directional_return = (
                signed_return
                if direction == "BULLISH"
                else -signed_return
            )

            abs_move = abs(
                signed_return
            )

            move_quality = min(
                100.0,
                max(
                    0.0,
                    abs_move / 0.50 * 80.0,
                ),
            )

            if directional_return > 0:

                move_quality += 20.0

            else:

                move_quality *= 0.35

            move_scores.append(
                min(
                    move_quality,
                    100.0,
                )
            )

            direction_votes.append(
                1.0
                if directional_return > 0
                else 0.0
            )

            # --------------------------------------------------------
            # Reversal detection
            # --------------------------------------------------------

            latest_open = opens[-1]
            latest_close = closes[-1]
            latest_high = highs[-1]
            latest_low = lows[-1]

            candle_range = max(
                latest_high - latest_low,
                1e-12,
            )

            body = abs(
                latest_close - latest_open
            )

            upper_wick = (
                latest_high
                - max(
                    latest_open,
                    latest_close,
                )
            )

            lower_wick = (
                min(
                    latest_open,
                    latest_close,
                )
                - latest_low
            )

            rejection = 0.0

            if (
                direction == "BULLISH"
                and lower_wick > body * 1.8
                and latest_close < latest_open
            ):

                rejection = 30.0

            elif (
                direction == "BEARISH"
                and upper_wick > body * 1.8
                and latest_close > latest_open
            ):

                rejection = 30.0

            wick_ratio = (
                max(
                    upper_wick,
                    lower_wick,
                )
                / candle_range
            )

            if wick_ratio > 0.65:

                rejection += 15.0

            indicator = tf_data.indicators

            if indicator is not None:

                if direction == "BULLISH":

                    if indicator.rsi >= 75:

                        rejection += 20.0

                    elif indicator.rsi >= 70:

                        rejection += 10.0

                    if indicator.macd_histogram < 0:

                        rejection += 12.0

                else:

                    if indicator.rsi <= 25:

                        rejection += 20.0

                    elif indicator.rsi <= 30:

                        rejection += 10.0

                    if indicator.macd_histogram > 0:

                        rejection += 12.0

            reversal_scores.append(
                min(
                    rejection,
                    100.0,
                )
            )

        if not move_scores:

            return 50.0, 35.0

        move_capture = (
            sum(move_scores)
            / len(move_scores)
        )

        reversal_risk = (
            sum(reversal_scores)
            / len(reversal_scores)
        )

        if direction_votes:

            directional_alignment = (
                sum(direction_votes)
                / len(direction_votes)
            )

            if directional_alignment < 0.34:

                reversal_risk += 28.0

            elif directional_alignment < 0.67:

                reversal_risk += 12.0

        return (
            round(
                min(
                    move_capture,
                    100.0,
                ),
                2,
            ),
            round(
                min(
                    reversal_risk,
                    100.0,
                ),
                2,
            ),
        )