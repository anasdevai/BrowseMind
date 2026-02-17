"""
Unit tests for encryption utilities
"""
import pytest
from app.db.encryption import encrypt, decrypt, generate_encryption_key


def test_encryption_decryption():
    """Test encryption and decryption"""
    original = "sensitive data"
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)

    assert encrypted != original
    assert decrypted == original


def test_encryption_different_outputs():
    """Test that same input produces different encrypted outputs"""
    data = "test data"
    encrypted1 = encrypt(data)
    encrypted2 = encrypt(data)

    # Should be different due to random IV
    assert encrypted1 != encrypted2

    # But both should decrypt to same value
    assert decrypt(encrypted1) == data
    assert decrypt(encrypted2) == data


def test_generate_encryption_key():
    """Test encryption key generation"""
    key = generate_encryption_key()

    assert isinstance(key, str)
    assert len(key) > 0


def test_decrypt_invalid_data():
    """Test decryption of invalid data"""
    with pytest.raises(Exception):
        decrypt("invalid encrypted data")


def test_encrypt_empty_string():
    """Test encryption of empty string"""
    encrypted = encrypt("")
    decrypted = decrypt(encrypted)

    assert decrypted == ""


def test_encrypt_unicode():
    """Test encryption of unicode characters"""
    original = "Hello 世界 🌍"
    encrypted = encrypt(original)
    decrypted = decrypt(encrypted)

    assert decrypted == original
