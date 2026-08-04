from dataclasses import asdict

from flask import Blueprint
from flask import jsonify
from flask import request

from app.pqi import pqi_state
from app.pqi.engine import engine


pqi_bp = Blueprint(
    "pqi",
    __name__,
)


@pqi_bp.route("/api/pqi/state")
def state():

    return jsonify(
        asdict(
            pqi_state
        )
    )


@pqi_bp.route(
    "/api/pqi/engage",
    methods=["POST"],
)
def engage():

    data = request.get_json() or {}

    engine.engage(
        exchange=data.get(
            "exchange",
            "Binance",
        ),
        market=data.get(
            "market",
            "BTCUSDT",
        ),
    )

    return jsonify(
        success=True
    )


@pqi_bp.route(
    "/api/pqi/pause",
    methods=["POST"],
)
def pause():

    engine.pause()

    return jsonify(
        success=True
    )


@pqi_bp.route(
    "/api/pqi/stop",
    methods=["POST"],
)
def stop():

    engine.stop()

    return jsonify(
        success=True
    )