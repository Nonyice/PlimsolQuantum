from flask import (
    render_template,
    redirect,
    url_for,
    request,
    flash,
)

from flask_login import (
    login_required,
    current_user,
)

from app.onboarding import onboarding_bp

from app.extensions import db


@onboarding_bp.route("/")
@login_required
def welcome():

    if current_user.onboarding_completed:

        return redirect(
            url_for("dashboard.index")
        )

    return render_template(
        "onboarding/welcome.html"
    )

@onboarding_bp.route("/complete", methods=["GET", "POST"])
@login_required
def complete():

    current_user.onboarding_completed = True

    current_user.pqi_enabled = True

    db.session.commit()

    flash(
        "Your PQI account is ready.",
        "success",
    )

    return redirect(
        url_for("dashboard.index")
    )