import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


class EncryptionService:
    """
    Handles encryption and decryption of sensitive data.
    """

    def __init__(self):
        key = os.getenv("ENCRYPTION_KEY")

        if not key:
            raise ValueError(
                "ENCRYPTION_KEY is missing from environment variables."
            )

        self.fernet = Fernet(key.encode())

    def encrypt(self, value: str) -> str:
        """
        Encrypt plain text.
        """
        return self.fernet.encrypt(value.encode()).decode()

    def decrypt(self, value: str) -> str:
        """
        Decrypt encrypted text.
        """
        return self.fernet.decrypt(value.encode()).decode()