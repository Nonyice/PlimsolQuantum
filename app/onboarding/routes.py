from __future__ import annotations

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.enums.exchange import Exchange
from app.enums.market import MarketType
from app.extensions import db
from app.models.trading_account import TradingAccount
from app.models.trial import Trial
from app.onboarding import onboarding_bp
from app.services.exchange_service import ExchangeService


TRIAL_DAYS = 7


def _onboarding_required():
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard.index"))
    return None


@onboarding_bp.route("/")
@login_required
def welcome():
    redirect_response = _onboarding_required()
    if redirect_response:
        return redirect_response
    return render_template("onboarding/welcome.html")


@onboarding_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    redirect_response = _onboarding_required()
    if redirect_response:
        return redirect_response

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        if not first_name or not last_name:
            flash("First name and last name are required.", "danger")
            return render_template("onboarding/profile.html")

        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.country = request.form.get("country", "").strip() or None
        current_user.timezone = request.form.get("timezone", "Africa/Lagos").strip() or "UTC"
        db.session.commit()

        return redirect(url_for("onboarding.account_type"))

    return render_template("onboarding/profile.html")


@onboarding_bp.route("/account-type")
@login_required
def account_type():
    redirect_response = _onboarding_required()
    if redirect_response:
        return redirect_response
    return render_template("onboarding/account_type.html", latest_trial=current_user.latest_trial)


@onboarding_bp.route("/trial", methods=["GET", "POST"])
@login_required
def trial():
    # Trial is the one onboarding action that is also allowed after
    # onboarding, because an expired trial may be renewed with another
    # seven-day trial.
    active_trial = current_user.active_trial
    if active_trial:
        flash("Your 7-day trial is already active.", "info")
        return redirect(url_for("dashboard.index"))

    # A user who is already onboarded can only reach this page to renew
    # an expired trial. A brand-new user can use it during onboarding.
    if current_user.onboarding_completed and current_user.account_type != "trial":
        flash("Start a new trial only after your previous trial has expired.", "warning")
        return redirect(url_for("dashboard.index"))

    latest_trial = current_user.latest_trial

    if request.method == "GET":
        return render_template("onboarding/trial.html", latest_trial=latest_trial)

    # Multiple trial records are intentional. The only restriction is that
    # there cannot be two active trials at the same time.
    if latest_trial and latest_trial.is_expired and latest_trial.status != "expired":
        latest_trial.expire()

    try:
        paper_capital = float(request.form.get("paper_capital", "1000"))
    except (TypeError, ValueError):
        paper_capital = 0
    if paper_capital < 10:
        flash("Minimum paper trading capital is $10.", "danger")
        return render_template("onboarding/trial.html", latest_trial=latest_trial)

    new_trial = Trial.create_trial(current_user.id, days=TRIAL_DAYS)
    current_user.account_type = "trial"
    current_user.pqi_enabled = True
    current_user.onboarding_completed = True
    session["pqi_paper_capital"] = paper_capital

    db.session.add(new_trial)
    db.session.commit()

    session.pop("onboarding_account_type", None)
    session.pop("onboarding_plan", None)
    session.pop("onboarding_exchange", None)
    session.pop("onboarding_testnet", None)
    session.pop("exchange_credentials_pending", None)

    flash("Your 7-day PQI trial has started.", "success")
    return redirect(url_for("dashboard.index"))


@onboarding_bp.route("/account-type/live", methods=["GET"])
@login_required
def select_live():
    redirect_response = _onboarding_required()
    if redirect_response:
        return redirect_response
    session["onboarding_account_type"] = "live"
    return redirect(url_for("onboarding.exchange"))


@onboarding_bp.route("/exchange", methods=["GET", "POST"])
@login_required
def exchange():
    redirect_response = _onboarding_required()
    if redirect_response:
        return redirect_response

    # Exchange credentials are collected only for the live path.
    session["onboarding_account_type"] = "live"

    if request.method == "POST":
        account_name = request.form.get("account_name", "My Exchange").strip() or "My Exchange"
        exchange_name = request.form.get("exchange", "").strip().lower()
        market_name = request.form.get("market_type", "spot").strip().lower()
        api_key = request.form.get("api_key", "").strip()
        api_secret = request.form.get("api_secret", request.form.get("secret_key", "")).strip()
        passphrase = request.form.get("passphrase", "").strip() or None
        testnet = request.form.get("testnet") == "1"

        if not exchange_name or not api_key or not api_secret:
            flash("Exchange, API key and API secret are required.", "danger")
            return render_template("onboarding/exchange.html")

        try:
            exchange = Exchange(exchange_name)
            market_type = MarketType(market_name)
        except ValueError:
            flash("Unsupported exchange or market type.", "danger")
            return render_template("onboarding/exchange.html")

        result = ExchangeService.test_connection(
            exchange=exchange,
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=testnet,
            market_type=market_type,
        )

        if not result["success"]:
            flash(f"Exchange validation failed: {result['message']}", "danger")
            return render_template("onboarding/exchange.html")

        account = TradingAccount(
            user_id=current_user.id,
            account_name=account_name,
            exchange=exchange,
            market_type=market_type,
            is_testnet=testnet,
            active=True,
            is_default=not TradingAccount.query.filter_by(user_id=current_user.id).first(),
            can_trade=False,
        )
        account.set_credentials(api_key, api_secret, passphrase)
        db.session.add(account)
        db.session.flush()

        current_user.account_type = "live"
        current_user.onboarding_completed = True
        current_user.pqi_enabled = True
        db.session.commit()

        session.pop("onboarding_account_type", None)
        session.pop("onboarding_plan", None)
        session.pop("onboarding_exchange", None)
        session.pop("onboarding_testnet", None)
        session.pop("exchange_credentials_pending", None)

        flash("Your live account is connected successfully. Trading is disabled until you explicitly authorize it.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("onboarding/exchange.html")


# Keep this route as a compatibility entry point for old bookmarks/forms.
@onboarding_bp.route("/account-type/trial", methods=["GET", "POST"])
@login_required
def select_trial():
    return redirect(url_for("onboarding.trial"))


@onboarding_bp.route("/subscription", methods=["GET", "POST"])
@login_required
def subscription():
    # GO LIVE enters here first. The gateway is deliberately kept in the live
    # path even when onboarding has already been completed.
    return render_template("onboarding/subscription.html")


@onboarding_bp.route("/complete")
@login_required
def complete():
    # Compatibility route for the old onboarding flow.
    if current_user.onboarding_completed:
        return redirect(url_for("dashboard.index"))
    return redirect(url_for("onboarding.account_type"))
