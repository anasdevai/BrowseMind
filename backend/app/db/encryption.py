"""
AES-256 encryption utilities for sensitive data fields.
Uses cryptography.fernet for symmetric encryption of conversation history,
assistant instructions, and other sensitive fields.
"""
import base64
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionError(Exception):
    """Raised when encryption/decryption operations fail."""
    pass


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive database fields.
    Uses AES-256 via Fernet (AES-128-CBC with HMAC).
    """

    def __init__(self, encryption_key: str):
        """
        Initialize encryption service with a base64-encoded key.

        Args:
            encryption_key: Base64-encoded 32-byte encryption key

        Raises:
            EncryptionError: If key is invalid
        """
        try:
            self._fernet = Fernet(encryption_key.encode())
        except Exception as e:
            raise EncryptionError(f"Invalid encryption key: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string to base64-encoded ciphertext.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            EncryptionError: If encryption fails
        """
        if not plaintext:
            return ""

        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode('utf-8'))
            return encrypted_bytes.decode('utf-8')
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt base64-encoded ciphertext to plaintext string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            EncryptionError: If decryption fails
        """
        if not ciphertext:
            return ""

        try:
            decrypted_bytes = self._fernet.decrypt(ciphertext.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            raise EncryptionError("Decryption failed: Invalid token or corrupted data")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")

    def encrypt_if_present(self, value: Optional[str]) -> Optional[str]:
        """
        Encrypt value if present, otherwise return None.

        Args:
            value: Optional string to encrypt

        Returns:
            Encrypted string or None
        """
        return self.encrypt(value) if value else None

    def decrypt_if_present(self, value: Optional[str]) -> Optional[str]:
        """
        Decrypt value if present, otherwise return None.

        Args:
            value: Optional encrypted string

        Returns:
            Decrypted string or None
        """
        return self.decrypt(value) if value else None


def generate_encryption_key() -> str:
    """
    Generate a new Fernet-compatible encryption key.

    Returns:
        Base64-encoded 32-byte key suitable for Fernet
    """
    return Fernet.generate_key().decode('utf-8')


def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
    """
    Derive a Fernet-compatible key from a password using PBKDF2.

    Args:
        password: Password to derive key from
        salt: Optional salt (generates random if not provided)

    Returns:
        Tuple of (base64-encoded key, salt used)
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,  # OWASP recommendation for 2024
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return key.decode('utf-8'), salt


# Global encryption service instance (initialized in main.py)
_encryption_service: Optional[EncryptionService] = None


def init_encryption(encryption_key: str) -> None:
    """
    Initialize the global encryption service.

    Args:
        encryption_key: Base64-encoded encryption key from config
    """
    global _encryption_service
    _encryption_service = EncryptionService(encryption_key)


def get_encryption_service() -> EncryptionService:
    """
    Get the global encryption service instance.

    Returns:
        Initialized EncryptionService

    Raises:
        RuntimeError: If encryption service not initialized
    """
    if _encryption_service is None:
        raise RuntimeError("Encryption service not initialized. Call init_encryption() first.")
    return _encryption_service
