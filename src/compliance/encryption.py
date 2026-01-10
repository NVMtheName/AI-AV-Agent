"""
Data Encryption Module for SOC 2 Compliance

This module provides encryption capabilities for sensitive data including:
- Log file encryption at rest
- Configuration file encryption
- Secure key management
- AES-256 encryption
"""

import base64
import hashlib
import os
from pathlib import Path
from typing import Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class DataEncryption:
    """
    Data encryption service for SOC 2 compliance.

    Features:
    - AES-256 encryption
    - Secure key derivation (PBKDF2)
    - File encryption/decryption
    - Automatic key management
    """

    def __init__(
        self,
        key_file: str = ".encryption_key",
        key_password: Optional[str] = None,
    ):
        """
        Initialize encryption service

        Args:
            key_file: Path to store the encryption key
            key_password: Password for key derivation (uses env var if not provided)
        """
        self.key_file = Path(key_file)
        self.key_password = key_password or os.getenv('AV_AGENT_ENCRYPTION_KEY', None)

        # Load or generate encryption key
        self.cipher_suite = self._load_or_generate_key()

    def _load_or_generate_key(self) -> Fernet:
        """Load existing key or generate new one"""
        if self.key_file.exists() and self.key_file.stat().st_size > 0:
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            if self.key_password:
                # Derive key from password
                key = self._derive_key_from_password(self.key_password)
            else:
                # Generate random key
                key = Fernet.generate_key()

            # Save key with restricted permissions
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)

            # Set restrictive permissions (owner read/write only)
            os.chmod(self.key_file, 0o600)

        return Fernet(key)

    def _derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """
        Derive encryption key from password using PBKDF2

        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if not provided)

        Returns:
            32-byte encryption key
        """
        if salt is None:
            salt = b'av-agent-salt-2024'  # Fixed salt for reproducibility

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP recommendation as of 2023
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt_data(self, data: Union[str, bytes]) -> bytes:
        """
        Encrypt data

        Args:
            data: Data to encrypt (string or bytes)

        Returns:
            Encrypted data
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        return self.cipher_suite.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt data

        Args:
            encrypted_data: Encrypted data

        Returns:
            Decrypted data
        """
        return self.cipher_suite.decrypt(encrypted_data)

    def encrypt_file(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        remove_original: bool = False,
    ) -> Path:
        """
        Encrypt a file

        Args:
            input_file: Path to file to encrypt
            output_file: Path for encrypted file (defaults to input_file.encrypted)
            remove_original: Whether to remove the original file after encryption

        Returns:
            Path to encrypted file
        """
        input_path = Path(input_file)
        if output_file is None:
            output_file = input_path.with_suffix(input_path.suffix + '.encrypted')
        else:
            output_file = Path(output_file)

        # Read and encrypt file
        with open(input_path, 'rb') as f:
            plaintext = f.read()

        ciphertext = self.encrypt_data(plaintext)

        # Write encrypted file
        with open(output_file, 'wb') as f:
            f.write(ciphertext)

        # Set restrictive permissions
        os.chmod(output_file, 0o600)

        # Remove original if requested
        if remove_original:
            input_path.unlink()

        return output_file

    def decrypt_file(
        self,
        input_file: Union[str, Path],
        output_file: Optional[Union[str, Path]] = None,
        remove_encrypted: bool = False,
    ) -> Path:
        """
        Decrypt a file

        Args:
            input_file: Path to encrypted file
            output_file: Path for decrypted file (defaults to input_file without .encrypted)
            remove_encrypted: Whether to remove encrypted file after decryption

        Returns:
            Path to decrypted file
        """
        input_path = Path(input_file)
        if output_file is None:
            # Remove .encrypted extension if present
            if input_path.suffix == '.encrypted':
                output_file = input_path.with_suffix('')
            else:
                output_file = input_path.with_suffix('.decrypted')
        else:
            output_file = Path(output_file)

        # Read and decrypt file
        with open(input_path, 'rb') as f:
            ciphertext = f.read()

        plaintext = self.decrypt_data(ciphertext)

        # Write decrypted file
        with open(output_file, 'wb') as f:
            f.write(plaintext)

        # Remove encrypted file if requested
        if remove_encrypted:
            input_path.unlink()

        return output_file

    def encrypt_string(self, plaintext: str) -> str:
        """
        Encrypt a string and return base64-encoded ciphertext

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        ciphertext = self.encrypt_data(plaintext)
        return base64.b64encode(ciphertext).decode('ascii')

    def decrypt_string(self, ciphertext: str) -> str:
        """
        Decrypt a base64-encoded ciphertext string

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted string
        """
        ciphertext_bytes = base64.b64decode(ciphertext.encode('ascii'))
        plaintext = self.decrypt_data(ciphertext_bytes)
        return plaintext.decode('utf-8')

    def hash_data(self, data: Union[str, bytes], algorithm: str = 'sha256') -> str:
        """
        Generate cryptographic hash of data

        Args:
            data: Data to hash
            algorithm: Hash algorithm (sha256, sha512, etc.)

        Returns:
            Hex-encoded hash digest
        """
        if isinstance(data, str):
            data = data.encode('utf-8')

        hash_func = hashlib.new(algorithm)
        hash_func.update(data)
        return hash_func.hexdigest()

    def verify_file_integrity(
        self,
        file_path: Union[str, Path],
        expected_hash: str,
        algorithm: str = 'sha256',
    ) -> bool:
        """
        Verify file integrity using hash

        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm used

        Returns:
            True if hash matches, False otherwise
        """
        with open(file_path, 'rb') as f:
            file_data = f.read()

        actual_hash = self.hash_data(file_data, algorithm)
        return actual_hash == expected_hash


# Utility functions for easy encryption/decryption
def encrypt_log_file(
    log_file: Union[str, Path],
    encryption_key: Optional[str] = None,
    remove_original: bool = False,
) -> Path:
    """
    Convenience function to encrypt a log file

    Args:
        log_file: Path to log file
        encryption_key: Encryption password (uses env var if not provided)
        remove_original: Whether to remove original file

    Returns:
        Path to encrypted file
    """
    encryptor = DataEncryption(key_password=encryption_key)
    return encryptor.encrypt_file(log_file, remove_original=remove_original)


def decrypt_log_file(
    encrypted_file: Union[str, Path],
    encryption_key: Optional[str] = None,
    remove_encrypted: bool = False,
) -> Path:
    """
    Convenience function to decrypt a log file

    Args:
        encrypted_file: Path to encrypted file
        encryption_key: Encryption password (uses env var if not provided)
        remove_encrypted: Whether to remove encrypted file

    Returns:
        Path to decrypted file
    """
    decryptor = DataEncryption(key_password=encryption_key)
    return decryptor.decrypt_file(encrypted_file, remove_encrypted=remove_encrypted)
