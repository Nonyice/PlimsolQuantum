from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, abort, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models.payment import Payment
from app.models.subscription import Subscription
from app.models.subscription_plan import SubscriptionPlan
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.subscription_service import SubscriptionService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return login_required(wrapped)


def _stats():
    active = Subscription.query.filter_by(status="ACTIVE").count()
    pending = Payment.query.filter(Payment.status.in_(["PENDING", "UNDER_REVIEW", "PAID"])).count()
    expired = Subscription.query.filter_by(status="EXPIRED").count()
    revenue = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0)).filter(Payment.status == "APPROVED").scalar() or 0
    return {"active": active, "pending": pending, "expired": expired, "revenue": Decimal(str(revenue))}


@admin_bp.route("/")
@admin_required
def index():
    return render_template("admin/index.html", stats=_stats(), payments=Payment.query.order_by(Payment.created_at.desc()).limit(12).all(), users=User.query.order_by(User.created_at.desc()).limit(12).all())


@admin_bp.route("/payments")
@admin_required
def payments():
    status = request.args.get("status")
    query = Payment.query.order_by(Payment.created_at.desc())
    if status:
        query = query.filter_by(status=status)
    return render_template("admin/payments.html", payments=query.limit(100).all(), status=status)


@admin_bp.route("/payments/<payment_id>/approve", methods=["POST"])
@admin_required
def approve_payment(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment or payment.method != "BANK_TRANSFER" or payment.status != "UNDER_REVIEW":
        abort(404)
    SubscriptionService.activate_payment(payment, current_user)
    db.session.add(AuditLog(actor_id=current_user.id, target_user_id=payment.user_id, action="PAYMENT_APPROVED", description=f"Approved payment {payment.reference}."))
    db.session.commit()
    flash("Payment approved and subscription activated.", "success")
    return redirect(request.referrer or url_for("admin.payments"))


@admin_bp.route("/payments/<payment_id>/reject", methods=["POST"])
@admin_required
def reject_payment(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        abort(404)
    reason = request.form.get("reason", "Payment could not be verified.").strip()
    payment.status = "REJECTED"
    payment.rejection_reason = reason
    payment.reviewed_at = datetime.utcnow()
    payment.reviewed_by = current_user.id
    db.session.add(AuditLog(actor_id=current_user.id, target_user_id=payment.user_id, action="PAYMENT_REJECTED", description=f"Rejected payment {payment.reference}: {reason}"))
    db.session.commit()
    flash("Payment rejected.", "warning")
    return redirect(request.referrer or url_for("admin.payments"))


@admin_bp.route("/payments/<payment_id>/evidence")
@admin_required
def evidence(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment or not payment.evidence_path:
        abort(404)
    return send_file(payment.evidence_path, as_attachment=False, download_name=payment.evidence_original_name or "payment-evidence")


@admin_bp.route("/customers")
@admin_required
def customers():
    q = request.args.get("q", "").strip()
    query = User.query.order_by(User.created_at.desc())
    if q:
        pattern = f"%{q}%"
        query = query.filter(db.or_(User.email.ilike(pattern), User.username.ilike(pattern), User.first_name.ilike(pattern), User.last_name.ilike(pattern)))
    return render_template("admin/customers.html", users=query.limit(200).all(), q=q)


@admin_bp.route("/customers/<user_id>")
@admin_required
def customer(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    return render_template(
        "admin/customer.html",
        customer=user,
        subscription=SubscriptionService.active_subscription(user),
        subscriptions=Subscription.query.filter_by(user_id=user.id).order_by(Subscription.start_date.desc()).all(),
        plans=SubscriptionPlan.query.filter_by(active=True, is_trial=False).order_by(SubscriptionPlan.duration_days.asc()).all(),
        payments=Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).all(),
    )


@admin_bp.route("/customers/<user_id>/extend", methods=["POST"])
@admin_required
def extend(user_id):
    user = db.session.get(User, user_id)
    subscription = SubscriptionService.active_subscription(user) if user else None
    if not user or not subscription:
        abort(404)
    try:
        days = max(1, int(request.form.get("days", "30")))
    except ValueError:
        days = 30
    subscription.end_date = subscription.end_date + timedelta(days=days)
    db.session.add(AuditLog(actor_id=current_user.id, target_user_id=user.id, action="SUBSCRIPTION_EXTENDED", description=f"Extended subscription by {days} days."))
    db.session.commit()
    flash(f"Subscription extended by {days} days.", "success")
    return redirect(url_for("admin.customer", user_id=user.id))


@admin_bp.route("/plans")
@admin_required
def plans():
    SubscriptionService.seed_plans()
    return render_template("admin/plans.html", plans=SubscriptionPlan.query.order_by(SubscriptionPlan.duration_days.asc()).all())
