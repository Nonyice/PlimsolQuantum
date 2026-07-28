from flask import request

from app.extensions import db
from app.models.activity_log import ActivityLog


class ActivityLogService:
    """
    Centralised activity logging.
    """

    @staticmethod
    def log(
        user,
        action,
        description="",
        status="SUCCESS",
    ):
        log = ActivityLog(
            user_id=user.id,
            action=action,
            description=description,
            endpoint=request.path if request else None,
            request_method=request.method if request else None,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string if request else None,
            status=status,
        )

        db.session.add(log)
        db.session.commit()