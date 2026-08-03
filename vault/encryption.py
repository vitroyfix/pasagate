import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from decouple import config


class VaultEncryption:
    """
    AES-256-GCM encryption for merchant credentials (Passkeys).
    GCM mode gives confidentiality AND integrity — tampered ciphertext
    fails decryption loudly instead of silently returning garbage.
    """

    def __init__(self):
        key_b64 = config("VAULT_ENCRYPTION_KEY")
        self._key = base64.urlsafe_b64decode(key_b64)
        if len(self._key) != 32:
            raise ValueError("VAULT_ENCRYPTION_KEY must decode to exactly 32 bytes")
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str) -> str:
        """Returns base64(nonce + ciphertext_with_tag) — one string, safe for a TextField."""
        nonce = os.urandom(12)  # fresh 96-bit nonce every call, standard for GCM
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def decrypt(self, stored_value: str) -> str:
        raw = base64.urlsafe_b64decode(stored_value)
        nonce, ciphertext = raw[:12], raw[12:]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()


vault = VaultEncryption()