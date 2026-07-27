from datetime import datetime


def utc_now():

    return datetime.utcnow()


def full_name(first_name, last_name):

    return f"{first_name} {last_name}".strip()