from flask import Blueprint
from flask import render_template

onboarding_bp = Blueprint(
    "onboarding",
    __name__,
)


@onboarding_bp.route("/onboarding/welcome")
def welcome():
    return render_template("onboarding/welcome.html")


@onboarding_bp.route("/onboarding/profile")
def profile():
    return render_template("onboarding/profile.html")


@onboarding_bp.route("/onboarding/account-type")
def account_type():
    return render_template("onboarding/account_type.html")


@onboarding_bp.route("/onboarding/exchange")
def exchange():
    return render_template("onboarding/exchange.html")


@onboarding_bp.route("/onboarding/subscription")
def subscription():
    return render_template("onboarding/subscription.html")


@onboarding_bp.route("/onboarding/complete")
def complete():
    return render_template("onboarding/complete.html")