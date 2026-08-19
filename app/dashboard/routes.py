from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    return render_template(
        "dashboard/index.html",
        latest_trial=current_user.latest_trial,
        active_trial=current_user.active_trial,
    )


@dashboard_bp.route("/trading")
@login_required
def trading():
    return render_template("trading/trade.html")


@dashboard_bp.route("/positions")
@login_required
def positions():
    return render_template("trading/positions.html")


@dashboard_bp.route("/orders")
@login_required
def orders():
    return render_template("trading/orders.html")


@dashboard_bp.route("/portfolio")
@login_required
def portfolio():
    return render_template("portfolio/index.html")


@dashboard_bp.route("/intelligence")
@login_required
def intelligence():
    return render_template("intelligence/index.html")


@dashboard_bp.route("/exchanges")
@login_required
def exchanges():
    return render_template("exchanges/index.html")


@dashboard_bp.route("/go-live")
@login_required
def go_live():
    # GO LIVE must pass through the subscription gateway before exchange setup.
    return redirect(url_for("onboarding.subscription"))


@dashboard_bp.route("/strategies")
@login_required
def strategies():
    return render_template("strategies/index.html")


@dashboard_bp.route("/risk")
@login_required
def risk():
    return render_template("risk/guardian.html")


@dashboard_bp.route("/reports")
@login_required
def reports():
    return render_template("reports/index.html")


@dashboard_bp.route("/settings")
@login_required
def settings():
    return render_template("settings/index.html")


@dashboard_bp.route("/signals")
@login_required
def signals():
    return render_template("signals/index.html")


@dashboard_bp.route("/backtesting")
@login_required
def backtesting():
    return render_template("backtesting/index.html")
