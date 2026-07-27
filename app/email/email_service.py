"""
Email Service.

Handles outgoing emails.
"""

from flask import current_app
from flask_mail import Message

from app.extensions import mail


class EmailService:

    @staticmethod
    def send_email(

        recipient,

        subject,

        html

    ):

        msg = Message(

            subject,

            recipients=[recipient],

            html=html,

            sender=current_app.config[
                "MAIL_DEFAULT_SENDER"
            ]

        )

        mail.send(msg)