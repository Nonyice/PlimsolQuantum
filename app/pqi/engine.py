from datetime import datetime, timedelta

from app.pqi import pqi_state


class PQIEngine:

    def engage(
        self,
        exchange,
        market,
    ):

        pqi_state.status = "ACTIVE"

        pqi_state.exchange = exchange

        pqi_state.market = market

        pqi_state.current_decision = "SCANNING"

        pqi_state.current_task = "Scanning Markets"

        pqi_state.next_scan = (
            datetime.utcnow() + timedelta(seconds=3)
        )

    def pause(self):

        pqi_state.status = "PAUSED"

        pqi_state.current_task = "Paused"

        pqi_state.current_decision = "WAITING"

    def stop(self):

        pqi_state.status = "STOPPED"

        pqi_state.current_task = "Stopped"

        pqi_state.current_decision = "IDLE"


engine = PQIEngine()