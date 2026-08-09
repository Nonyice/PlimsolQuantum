from flask import (
    Blueprint,
    render_template,
)


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
)


@dashboard_bp.route("/")
def index():

    return render_template(
        "dashboard/index.html"
    )


@dashboard_bp.route("/trading")
def trading():

    return render_template(
        "trading/trade.html"
    )


@dashboard_bp.route("/positions")
def positions():

    return render_template(
        "trading/positions.html"
    )


@dashboard_bp.route("/orders")
def orders():

    return render_template(
        "trading/orders.html"
    )


@dashboard_bp.route("/portfolio")
def portfolio():

    return render_template(
        "portfolio/index.html"
    )


@dashboard_bp.route("/intelligence")
def intelligence():

    return render_template(
        "intelligence/index.html"
    )


@dashboard_bp.route("/exchanges")
def exchanges():

    return render_template(
        "exchanges/index.html"
    )


@dashboard_bp.route("/strategies")
def strategies():

    return render_template(
        "strategies/index.html"
    )


@dashboard_bp.route("/risk")
def risk():

    return render_template(
        "risk/guardian.html"
    )


@dashboard_bp.route("/reports")
def reports():

    return render_template(
        "reports/index.html"
    )


@dashboard_bp.route("/settings")
def settings():

    return render_template(
        "settings/index.html"
    )


@dashboard_bp.route("/signals")
def signals():

    return render_template(
        "signals/index.html"
    )


@dashboard_bp.route("/backtesting")
def backtesting():

    return render_template(
        "backtesting/index.html"
    )