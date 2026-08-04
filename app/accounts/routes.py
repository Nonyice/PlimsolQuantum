from flask import Blueprint
from flask import render_template


accounts_bp = Blueprint(
    "accounts",
    __name__,
)


@accounts_bp.route("/accounts")
def index():

    return render_template(
        "accounts/index.html"
    )