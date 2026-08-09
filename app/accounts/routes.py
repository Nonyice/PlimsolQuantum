from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from flask_login import login_required

from app.accounts import accounts_bp


@accounts_bp.route("/")
@login_required
def index():

    return render_template(
        "accounts/index.html"
    )


@accounts_bp.route(
    "/add",
    methods=["GET", "POST"],
)
@login_required
def add():

    if request.method == "POST":

        # Exchange connection logic
        # will be added here.

        flash(
            "Exchange connection received.",
            "success",
        )

        return redirect(
            url_for("accounts.index")
        )

    return render_template(
        "accounts/add.html"
    )