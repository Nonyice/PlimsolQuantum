from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.accounts import accounts_bp
from app.enums.exchange import Exchange
from app.enums.market import MarketType
from app.extensions import db
from app.models.trading_account import TradingAccount
from app.services.exchange_service import ExchangeService


@accounts_bp.route("/")
@login_required
def index():
    accounts = (
        TradingAccount.query
        .filter_by(user_id=current_user.id)
        .order_by(TradingAccount.created_at.desc())
        .all()
    )
    return render_template("accounts/index.html", accounts=accounts)


@accounts_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        account_name = request.form.get("account_name", "").strip()
        exchange_name = request.form.get("exchange", "").strip().lower()
        market_name = request.form.get("market_type", "spot").strip().lower()
        api_key = request.form.get("api_key", "").strip()
        api_secret = request.form.get("api_secret", "").strip()
        passphrase = request.form.get("passphrase", "").strip() or None
        is_testnet = request.form.get("is_testnet") == "1"

        if not account_name or not exchange_name or not api_key or not api_secret:
            flash("Account name, exchange, API key and API secret are required.", "danger")
            return render_template("accounts/add.html")

        try:
            exchange = Exchange(exchange_name)
            market_type = MarketType(market_name)
        except ValueError:
            flash("Unsupported exchange or market type.", "danger")
            return render_template("accounts/add.html")

        result = ExchangeService.test_connection(
            exchange=exchange,
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            testnet=is_testnet,
            market_type=market_type,
        )

        if not result["success"]:
            flash(f"Exchange connection failed: {result['message']}", "danger")
            return render_template("accounts/add.html")

        account = TradingAccount(
            user_id=current_user.id,
            account_name=account_name,
            exchange=exchange,
            market_type=market_type,
            is_testnet=is_testnet,
            active=True,
            is_default=not TradingAccount.query.filter_by(user_id=current_user.id).first(),
            can_trade=False,
        )
        account.set_credentials(api_key, api_secret, passphrase)

        db.session.add(account)
        db.session.commit()

        flash("Exchange connected successfully. Trading remains disabled until explicitly authorized.", "success")
        return redirect(url_for("accounts.index"))

    return render_template("accounts/add.html")
