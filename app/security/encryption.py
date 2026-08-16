import os

from cryptography.fernet import Fernet


class EncryptionError(Exception):
    """Raised when encryption configuration or operations fail."""


def _get_cipher():
    key = os.getenv("PQI_ENCRYPTION_KEY")

    if not key:
        raise EncryptionError(
            "PQI_ENCRYPTION_KEY is not configured."
        )

    try:
        return Fernet(key.encode("utf-8"))
    except Exception as exc:
        raise EncryptionError(
            "PQI_ENCRYPTION_KEY is invalid."
        ) from exc


def encrypt_value(value: str) -> str:
    """
    Encrypt a sensitive value before storing it in the database.
    """

    if not value:
        raise EncryptionError(
            "Cannot encrypt an empty value."
        )

    cipher = _get_cipher()

    return cipher.encrypt(
        value.encode("utf-8")
    ).decode("utf-8")


def decrypt_value(value: str) -> str:
    """
    Decrypt a value retrieved from the database.
    """

    if not value:
        raise EncryptionError(
            "Cannot decrypt an empty value."
        )

    cipher = _get_cipher()

    try:
        return cipher.decrypt(
            value.encode("utf-8")
        ).decode("utf-8")

    except Exception as exc:
        raise EncryptionError(
            "Unable to decrypt stored credential."
        ) from exc