"""Encryption at rest for stored files.

Envelope encryption:
  * every file gets its own random 256-bit data key (DEK);
  * the file is encrypted with AES-256-GCM using that DEK;
  * the DEK itself is encrypted ("wrapped") with the server master key and stored
    in the database next to the file record.

A stolen copy of the ``uploads/`` folder is therefore useless without the master
key, and rotating the master key only requires re-wrapping the small DEKs, not
re-encrypting every file. AES-GCM is authenticated, so any tampering with the
ciphertext is detected on decryption.
"""
from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12  # 96-bit nonce, recommended size for GCM


class DecryptionError(Exception):
    """Raised when a file or key cannot be authenticated/decrypted."""


def load_master_key(value: str | None) -> bytes:
    """Decode the base64 master key from configuration (must be 32 bytes)."""
    if not value:
        raise ValueError("MASTER_KEY is not set")
    key = base64.urlsafe_b64decode(value)
    if len(key) != 32:
        raise ValueError("MASTER_KEY must decode to exactly 32 bytes")
    return key


def generate_master_key() -> str:
    """Return a new random master key, base64-encoded, for the .env file."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def encrypt_file(plaintext: bytes, master_key: bytes, file_id: str) -> tuple[bytes, bytes]:
    """Encrypt ``plaintext``.

    Returns ``(ciphertext_blob, wrapped_key)`` where ``ciphertext_blob`` is
    ``nonce || ciphertext+tag``. ``file_id`` is bound as associated data so a
    ciphertext cannot be swapped onto another file record.
    """
    dek = AESGCM.generate_key(bit_length=256)
    aad = file_id.encode()

    nonce = os.urandom(NONCE_SIZE)
    blob = nonce + AESGCM(dek).encrypt(nonce, plaintext, aad)

    key_nonce = os.urandom(NONCE_SIZE)
    wrapped = key_nonce + AESGCM(master_key).encrypt(key_nonce, dek, aad)
    return blob, wrapped


def decrypt_file(blob: bytes, wrapped_key: bytes, master_key: bytes, file_id: str) -> bytes:
    """Reverse of :func:`encrypt_file`. Raises :class:`DecryptionError` on tampering."""
    aad = file_id.encode()
    try:
        dek = AESGCM(master_key).decrypt(wrapped_key[:NONCE_SIZE], wrapped_key[NONCE_SIZE:], aad)
        return AESGCM(dek).decrypt(blob[:NONCE_SIZE], blob[NONCE_SIZE:], aad)
    except Exception as exc:  # InvalidTag, wrong lengths, ...
        raise DecryptionError("file failed authentication") from exc
