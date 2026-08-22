from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import requests
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.extensions import db, csrf
from app.models.payment import Payment
from app.models.subscription_plan import SubscriptionPlan
from app.services.subscription_service import SubscriptionService

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")

ALLOWED_EVIDENCE = {"pdf", "png", "jpg", "jpeg", "webp"}


def _plans():
    plans = SubscriptionPlan.query.filter_by(active=True, is_trial=False).order_by(SubscriptionPlan.duration_days.asc()).all()
    if len(plans) < 3:
        SubscriptionService.seed_plans()
        plans = SubscriptionPlan.query.filter_by(active=True, is_trial=False).order_by(SubscriptionPlan.duration_days.asc()).all()
    return plans


def _paystack_headers():
    return {"Authorization": f"Bearer {current_app.config.get('PAYSTACK_SECRET_KEY', '')}", "Content-Type": "application/json"}


@billing_bp.route("/plans")
@login_required
def plans():
    active = SubscriptionService.active_subscription(current_user)
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).limit(10).all()
    return render_template("billing/plans.html", plans=_plans(), active_subscription=active, payments=payments)


@billing_bp.route("/paystack/initialize/<plan_id>", methods=["POST"])
@login_required
def paystack_initialize(plan_id):
    plan = db.session.get(SubscriptionPlan, plan_id)
    if not plan or not plan.active or plan.is_trial:
        flash("That subscription plan is no longer available.", "danger")
        return redirect(url_for("billing.plans"))
    secret = current_app.config.get("PAYSTACK_SECRET_KEY")
    if not secret:
        flash("Paystack is not configured yet. Please use bank transfer or contact support.", "warning")
        return redirect(url_for("billing.plans"))

    payment = SubscriptionService.new_payment(current_user, plan, "PAYSTACK")
    payload = {
        "email": current_user.email,
        "amount": int(Decimal(str(plan.price)) * 100),
        "currency": plan.currency or "USD",
        "reference": payment.reference,
        "callback_url": url_for("billing.paystack_callback", _external=True),
        "metadata": {"payment_reference": payment.reference, "plan_id": str(plan.id), "user_id": str(current_user.id)},
    }
    try:
        response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=_paystack_headers(), timeout=20)
        data = response.json()
    except Exception as exc:
        payment.status = "FAILED"
        payment.admin_notes = str(exc)
        db.session.commit()
        flash("Unable to initialize Paystack right now. Please try again.", "danger")
        return redirect(url_for("billing.plans"))

    if not response.ok or not data.get("status"):
        payment.status = "FAILED"
        payment.admin_notes = data.get("message", "Paystack initialization failed")
        db.session.commit()
        flash("Paystack could not start the payment.", "danger")
        return redirect(url_for("billing.plans"))
    return redirect(data["data"]["authorization_url"])


@billing_bp.route("/paystack/callback")
@login_required
def paystack_callback():
    reference = request.args.get("reference", "").strip()
    payment = Payment.query.filter_by(reference=reference, user_id=current_user.id).first()
    if not payment:
        flash("Payment reference could not be found.", "danger")
        return redirect(url_for("billing.plans"))
    secret = current_app.config.get("PAYSTACK_SECRET_KEY")
    if not secret:
        flash("Paystack is not configured.", "danger")
        return redirect(url_for("billing.plans"))
    try:
        response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=_paystack_headers(), timeout=20)
        data = response.json()
    except Exception:
        flash("We could not verify the Paystack transaction yet. Please check your subscription page shortly.", "warning")
        return redirect(url_for("billing.plans"))
    if response.ok and data.get("status") and data.get("data", {}).get("status") == "success":
        payment.status = "PAID"
        payment.provider_reference = str(data["data"].get("id") or reference)
        payment.paid_at = datetime.utcnow()
        db.session.commit()
        SubscriptionService.activate_payment(payment)
        flash("Payment verified. Your PQI subscription is now active.", "success")
        if not current_user.onboarding_completed:
            return redirect(url_for("onboarding.exchange"))
        return redirect(url_for("dashboard.index"))
    payment.status = "FAILED"
    db.session.commit()
    flash("Paystack did not confirm a successful payment.", "danger")
    return redirect(url_for("billing.plans"))


@billing_bp.route("/paystack/webhook", methods=["POST"])
@csrf.exempt
def paystack_webhook():
    secret = current_app.config.get("PAYSTACK_SECRET_KEY", "")
    signature = request.headers.get("x-paystack-signature", "")
    digest = hmac.new(secret.encode(), request.get_data(), hashlib.sha512).hexdigest()
    if not secret or not hmac.compare_digest(digest, signature):
        return jsonify({"success": False}), 401

    payload = request.get_json(silent=True) or {}
    if payload.get("event") != "charge.success":
        return jsonify({"success": True})
    data = payload.get("data") or {}
    reference = data.get("reference")
    payment = Payment.query.filter_by(reference=reference).first()
    if payment and payment.status not in {"APPROVED", "PAID"}:
        payment.status = "PAID"
        payment.provider_reference = str(data.get("id") or reference)
        payment.paid_at = datetime.utcnow()
        db.session.commit()
        SubscriptionService.activate_payment(payment)
    return jsonify({"success": True})


@billing_bp.route("/bank-transfer/<plan_id>", methods=["POST"])
@login_required
def bank_transfer(plan_id):
    plan = db.session.get(SubscriptionPlan, plan_id)
    if not plan or not plan.active or plan.is_trial:
        flash("That subscription plan is no longer available.", "danger")
        return redirect(url_for("billing.plans"))
    payment = SubscriptionService.new_payment(current_user, plan, "BANK_TRANSFER")
    flash(f"Bank transfer reference {payment.reference} created. Upload your payment evidence below.", "info")
    return redirect(url_for("billing.evidence", payment_id=payment.id))


@billing_bp.route("/evidence/<payment_id>", methods=["GET", "POST"])
@login_required
def evidence(payment_id):
    payment = Payment.query.filter_by(id=payment_id, user_id=current_user.id, method="BANK_TRANSFER").first_or_404()
    if request.method == "POST":
        file = request.files.get("evidence")
        if not file or not file.filename:
            flash("Select your transfer evidence first.", "danger")
            return redirect(url_for("billing.evidence", payment_id=payment.id))
        ext = Path(file.filename).suffix.lower().lstrip(".")
        if ext not in ALLOWED_EVIDENCE:
            flash("Evidence must be PDF, PNG, JPG or WEBP.", "danger")
            return redirect(url_for("billing.evidence", payment_id=payment.id))
        upload_root = Path(current_app.instance_path) / "private" / "payments"
        upload_root.mkdir(parents=True, exist_ok=True)
        filename = f"{payment.reference}.{ext}"
        path = upload_root / secure_filename(filename)
        file.save(path)
        payment.evidence_path = str(path)
        payment.evidence_original_name = secure_filename(file.filename)
        payment.status = "UNDER_REVIEW"
        db.session.commit()
        flash("Payment evidence submitted. An administrator will verify the transfer.", "success")
        return redirect(url_for("billing.plans"))
    return render_template("billing/evidence.html", payment=payment)
