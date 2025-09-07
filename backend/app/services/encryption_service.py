from typing import Dict, Any, Optional, Union, List
import base64
import json
import os
import hashlib
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import secrets
import logging

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Custom exception for encryption-related errors"""
    pass


class KeyDerivationError(EncryptionError):
    """Exception raised when key derivation fails"""
    pass


class EncryptionMethod:
    """Encryption method constants"""
    AES_256_GCM = "aes_256_gcm"
    FERNET = "fernet"
    RSA_OAEP = "rsa_oaep"
    HYBRID = "hybrid"  # RSA + AES for large data


class DataEncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        self.default_method = EncryptionMethod.AES_256_GCM
        
        # In production, get these from GCP Secret Manager
        self.master_key = self._get_or_generate_master_key()
        
        # Key derivation settings
        self.kdf_iterations = 100000
        self.salt_length = 16
        
        # Encryption metadata
        self.version = "1.0"
        
    def encrypt_sensitive_data(
        self,
        data: Union[str, bytes, Dict[str, Any]],
        encryption_method: str = None,
        additional_context: Dict[str, str] = None
    ) -> Dict[str, str]:
        """
        Encrypt sensitive data and return encrypted package
        
        Args:
            data: Data to encrypt (string, bytes, or dict)
            encryption_method: Method to use for encryption
            additional_context: Additional context for encryption (user_id, etc.)
            
        Returns:
            Dict containing encrypted data and metadata
        """
        
        method = encryption_method or self.default_method
        
        try:
            # Prepare data for encryption
            if isinstance(data, dict):
                plaintext = json.dumps(data, separators=(',', ':')).encode('utf-8')
                data_type = "json"
            elif isinstance(data, str):
                plaintext = data.encode('utf-8')
                data_type = "string"
            elif isinstance(data, bytes):
                plaintext = data
                data_type = "bytes"
            else:
                raise EncryptionError(f"Unsupported data type: {type(data)}")
            
            # Encrypt based on method
            if method == EncryptionMethod.AES_256_GCM:
                encrypted_result = self._encrypt_aes_gcm(plaintext)
            elif method == EncryptionMethod.FERNET:
                encrypted_result = self._encrypt_fernet(plaintext)
            elif method == EncryptionMethod.HYBRID:
                encrypted_result = self._encrypt_hybrid(plaintext)
            else:
                raise EncryptionError(f"Unsupported encryption method: {method}")
            
            # Create encryption package
            encryption_package = {
                "encrypted_data": encrypted_result["ciphertext"],
                "method": method,
                "version": self.version,
                "data_type": data_type,
                "encrypted_at": datetime.utcnow().isoformat(),
                "checksum": self._calculate_checksum(plaintext),
                **encrypted_result["metadata"]
            }
            
            # Add additional context if provided
            if additional_context:
                encryption_package["context"] = additional_context
            
            logger.debug(f"Data encrypted successfully using {method}")
            
            return encryption_package
            
        except Exception as e:
            logger.error(f"Failed to encrypt data: {str(e)}")
            raise EncryptionError(f"Encryption failed: {str(e)}")
    
    def decrypt_sensitive_data(
        self,
        encryption_package: Dict[str, str],
        expected_data_type: str = None
    ) -> Union[str, bytes, Dict[str, Any]]:
        """
        Decrypt data from encryption package
        
        Args:
            encryption_package: Package containing encrypted data and metadata
            expected_data_type: Expected type of decrypted data for validation
            
        Returns:
            Decrypted data in original format
        """
        
        try:
            method = encryption_package.get("method")
            version = encryption_package.get("version")
            data_type = encryption_package.get("data_type")
            encrypted_data = encryption_package.get("encrypted_data")
            original_checksum = encryption_package.get("checksum")
            
            # Validate package
            if not all([method, version, data_type, encrypted_data]):
                raise EncryptionError("Invalid encryption package: missing required fields")
            
            if version != self.version:
                logger.warning(f"Version mismatch: package={version}, current={self.version}")
            
            # Decrypt based on method
            if method == EncryptionMethod.AES_256_GCM:
                plaintext = self._decrypt_aes_gcm(encrypted_data, encryption_package)
            elif method == EncryptionMethod.FERNET:
                plaintext = self._decrypt_fernet(encrypted_data, encryption_package)
            elif method == EncryptionMethod.HYBRID:
                plaintext = self._decrypt_hybrid(encrypted_data, encryption_package)
            else:
                raise EncryptionError(f"Unsupported decryption method: {method}")
            
            # Verify checksum if available
            if original_checksum:
                current_checksum = self._calculate_checksum(plaintext)
                if current_checksum != original_checksum:
                    raise EncryptionError("Data integrity check failed: checksum mismatch")
            
            # Convert back to original data type
            if data_type == "json":
                result = json.loads(plaintext.decode('utf-8'))
            elif data_type == "string":
                result = plaintext.decode('utf-8')
            elif data_type == "bytes":
                result = plaintext
            else:
                raise EncryptionError(f"Unknown data type: {data_type}")
            
            # Validate expected type if provided
            if expected_data_type and data_type != expected_data_type:
                raise EncryptionError(f"Type mismatch: expected {expected_data_type}, got {data_type}")
            
            logger.debug(f"Data decrypted successfully using {method}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse decrypted JSON: {str(e)}")
            raise EncryptionError(f"Invalid JSON in decrypted data: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to decrypt data: {str(e)}")
            raise EncryptionError(f"Decryption failed: {str(e)}")
    
    def _encrypt_aes_gcm(self, plaintext: bytes) -> Dict[str, Any]:
        """Encrypt using AES-256-GCM"""
        
        # Generate random key and IV
        key = secrets.token_bytes(32)  # 256-bit key
        iv = secrets.token_bytes(12)   # 96-bit IV for GCM
        
        # Encrypt data
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        # Get authentication tag
        auth_tag = encryptor.tag
        
        # Encrypt the data key with master key
        encrypted_key = self._encrypt_key(key)
        
        # Combine all components
        combined_data = base64.b64encode(
            iv + auth_tag + ciphertext
        ).decode('ascii')
        
        return {
            "ciphertext": combined_data,
            "metadata": {
                "encrypted_key": encrypted_key,
                "algorithm": "AES-256-GCM",
                "key_length": 32,
                "iv_length": 12
            }
        }
    
    def _decrypt_aes_gcm(self, encrypted_data: str, package: Dict[str, str]) -> bytes:
        """Decrypt using AES-256-GCM"""
        
        try:
            # Decode combined data
            combined_data = base64.b64decode(encrypted_data.encode('ascii'))
            
            # Extract components
            iv = combined_data[:12]
            auth_tag = combined_data[12:28]
            ciphertext = combined_data[28:]
            
            # Decrypt the data key
            encrypted_key = package.get("encrypted_key")
            if not encrypted_key:
                raise EncryptionError("Missing encrypted key in package")
            
            key = self._decrypt_key(encrypted_key)
            
            # Decrypt data
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, auth_tag))
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext
            
        except Exception as e:
            raise EncryptionError(f"AES-GCM decryption failed: {str(e)}")
    
    def _encrypt_fernet(self, plaintext: bytes) -> Dict[str, Any]:
        """Encrypt using Fernet (symmetric encryption)"""
        
        # Generate Fernet key from master key
        fernet_key = self._derive_fernet_key()
        f = Fernet(fernet_key)
        
        # Encrypt data
        ciphertext = f.encrypt(plaintext)
        
        return {
            "ciphertext": base64.b64encode(ciphertext).decode('ascii'),
            "metadata": {
                "algorithm": "Fernet",
                "kdf": "PBKDF2-HMAC-SHA256"
            }
        }
    
    def _decrypt_fernet(self, encrypted_data: str, package: Dict[str, str]) -> bytes:
        """Decrypt using Fernet"""
        
        try:
            # Generate same Fernet key
            fernet_key = self._derive_fernet_key()
            f = Fernet(fernet_key)
            
            # Decode and decrypt
            ciphertext = base64.b64decode(encrypted_data.encode('ascii'))
            plaintext = f.decrypt(ciphertext)
            
            return plaintext
            
        except Exception as e:
            raise EncryptionError(f"Fernet decryption failed: {str(e)}")
    
    def _encrypt_hybrid(self, plaintext: bytes) -> Dict[str, Any]:
        """Encrypt using hybrid RSA + AES for large data"""
        
        # Generate random AES key
        aes_key = secrets.token_bytes(32)
        
        # Encrypt data with AES
        aes_result = self._encrypt_with_aes_key(plaintext, aes_key)
        
        # Encrypt AES key with RSA
        rsa_key = self._get_rsa_public_key()
        encrypted_aes_key = rsa_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        return {
            "ciphertext": aes_result["ciphertext"],
            "metadata": {
                "encrypted_key": base64.b64encode(encrypted_aes_key).decode('ascii'),
                "algorithm": "RSA-OAEP + AES-256-GCM",
                "rsa_key_size": 2048,
                **aes_result["metadata"]
            }
        }
    
    def _decrypt_hybrid(self, encrypted_data: str, package: Dict[str, str]) -> bytes:
        """Decrypt using hybrid RSA + AES"""
        
        try:
            # Get encrypted AES key
            encrypted_aes_key_b64 = package.get("encrypted_key")
            if not encrypted_aes_key_b64:
                raise EncryptionError("Missing encrypted AES key")
            
            encrypted_aes_key = base64.b64decode(encrypted_aes_key_b64)
            
            # Decrypt AES key with RSA
            rsa_private_key = self._get_rsa_private_key()
            aes_key = rsa_private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # Decrypt data with AES key
            plaintext = self._decrypt_with_aes_key(encrypted_data, aes_key, package)
            
            return plaintext
            
        except Exception as e:
            raise EncryptionError(f"Hybrid decryption failed: {str(e)}")
    
    def _encrypt_key(self, key: bytes) -> str:
        """Encrypt a data key with master key"""
        
        # Use Fernet with master key for key encryption
        master_fernet = self._get_master_fernet()
        encrypted_key = master_fernet.encrypt(key)
        
        return base64.b64encode(encrypted_key).decode('ascii')
    
    def _decrypt_key(self, encrypted_key: str) -> bytes:
        """Decrypt a data key with master key"""
        
        master_fernet = self._get_master_fernet()
        encrypted_key_bytes = base64.b64decode(encrypted_key.encode('ascii'))
        
        return master_fernet.decrypt(encrypted_key_bytes)
    
    def _get_or_generate_master_key(self) -> bytes:
        """Get or generate master encryption key"""
        
        # In production, this would be retrieved from GCP Secret Manager
        # For development, generate or load from environment
        
        master_key_b64 = os.getenv('ENCRYPTION_MASTER_KEY')
        
        if master_key_b64:
            try:
                return base64.b64decode(master_key_b64)
            except Exception as e:
                logger.warning(f"Invalid master key in environment: {e}")
        
        # Generate new master key for development
        master_key = secrets.token_bytes(32)
        logger.warning("Generated new master key for development. Set ENCRYPTION_MASTER_KEY environment variable for production.")
        
        return master_key
    
    def _get_master_fernet(self) -> Fernet:
        """Get Fernet instance using master key"""
        
        # Derive Fernet key from master key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'master_key_salt_v1',  # Fixed salt for master key
            iterations=self.kdf_iterations,
        )
        
        fernet_key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        return Fernet(fernet_key)
    
    def _derive_fernet_key(self, context: str = "default") -> bytes:
        """Derive Fernet key from master key with context"""
        
        salt = f"fernet_{context}_salt_v1".encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=self.kdf_iterations,
        )
        
        return base64.urlsafe_b64encode(kdf.derive(self.master_key))
    
    def _get_rsa_public_key(self):
        """Get RSA public key for hybrid encryption"""
        
        # In production, load from secure storage
        # For development, generate ephemeral key pair
        
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Store private key for decryption (in production, use secure storage)
        self._rsa_private_key = private_key
        
        return private_key.public_key()
    
    def _get_rsa_private_key(self):
        """Get RSA private key for hybrid decryption"""
        
        if hasattr(self, '_rsa_private_key'):
            return self._rsa_private_key
        
        raise EncryptionError("RSA private key not available")
    
    def _encrypt_with_aes_key(self, plaintext: bytes, key: bytes) -> Dict[str, Any]:
        """Encrypt data with provided AES key"""
        
        iv = secrets.token_bytes(12)
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        auth_tag = encryptor.tag
        
        combined_data = base64.b64encode(iv + auth_tag + ciphertext).decode('ascii')
        
        return {
            "ciphertext": combined_data,
            "metadata": {
                "iv_length": 12,
                "tag_length": 16
            }
        }
    
    def _decrypt_with_aes_key(self, encrypted_data: str, key: bytes, package: Dict[str, str]) -> bytes:
        """Decrypt data with provided AES key"""
        
        combined_data = base64.b64decode(encrypted_data.encode('ascii'))
        
        iv = combined_data[:12]
        auth_tag = combined_data[12:28]
        ciphertext = combined_data[28:]
        
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, auth_tag))
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA256 checksum of data"""
        
        return hashlib.sha256(data).hexdigest()
    
    def encrypt_field(self, field_value: Any, field_name: str = "unknown") -> Dict[str, str]:
        """Encrypt a single database field"""
        
        return self.encrypt_sensitive_data(
            field_value,
            additional_context={"field_name": field_name}
        )
    
    def decrypt_field(self, encrypted_field: Dict[str, str]) -> Any:
        """Decrypt a single database field"""
        
        return self.decrypt_sensitive_data(encrypted_field)
    
    def rotate_encryption_keys(self) -> Dict[str, Any]:
        """Rotate encryption keys (admin function)"""
        
        # This is a complex operation that would:
        # 1. Generate new master key
        # 2. Re-encrypt all data with new key
        # 3. Update key in secret manager
        # 4. Clean up old keys
        
        logger.warning("Key rotation not implemented in demo version")
        
        return {
            "status": "not_implemented",
            "message": "Key rotation requires production deployment with proper key management"
        }


class FieldEncryptionMixin:
    """Mixin for SQLAlchemy models to support field-level encryption"""
    
    @staticmethod
    def encrypt_field_value(value: Any, field_name: str) -> Dict[str, str]:
        """Encrypt a field value"""
        
        if value is None:
            return None
        
        encryption_service = DataEncryptionService()
        return encryption_service.encrypt_field(value, field_name)
    
    @staticmethod
    def decrypt_field_value(encrypted_value: Dict[str, str]) -> Any:
        """Decrypt a field value"""
        
        if encrypted_value is None:
            return None
        
        encryption_service = DataEncryptionService()
        return encryption_service.decrypt_field(encrypted_value)


# Utility functions for common encryption patterns

def encrypt_user_data(user_data: Dict[str, Any], user_id: str) -> Dict[str, str]:
    """Encrypt user data with user context"""
    
    service = DataEncryptionService()
    return service.encrypt_sensitive_data(
        user_data,
        additional_context={"user_id": user_id, "data_type": "user_data"}
    )


def decrypt_user_data(encrypted_data: Dict[str, str], user_id: str) -> Dict[str, Any]:
    """Decrypt user data and verify user context"""
    
    service = DataEncryptionService()
    result = service.decrypt_sensitive_data(encrypted_data, expected_data_type="json")
    
    # Verify user context if present
    context = encrypted_data.get("context", {})
    if context.get("user_id") and context["user_id"] != user_id:
        raise EncryptionError("User ID mismatch in encrypted data context")
    
    return result


def encrypt_api_keys(api_keys: Dict[str, str]) -> Dict[str, str]:
    """Encrypt API keys for secure storage"""
    
    service = DataEncryptionService()
    return service.encrypt_sensitive_data(
        api_keys,
        encryption_method=EncryptionMethod.AES_256_GCM,
        additional_context={"data_type": "api_keys"}
    )


def decrypt_api_keys(encrypted_keys: Dict[str, str]) -> Dict[str, str]:
    """Decrypt API keys"""
    
    service = DataEncryptionService()
    return service.decrypt_sensitive_data(encrypted_keys, expected_data_type="json")


# Configuration encryption for sensitive settings
class ConfigurationEncryption:
    """Encrypt configuration values containing sensitive information"""
    
    def __init__(self):
        self.service = DataEncryptionService()
        self.sensitive_keys = {
            'database_url', 'redis_url', 'jwt_secret_key', 
            'gemini_api_key', 'sendgrid_api_key',
            'password', 'secret', 'token', 'key'
        }
    
    def encrypt_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive values in configuration"""
        
        encrypted_config = {}
        
        for key, value in config.items():
            if self._is_sensitive_key(key) and isinstance(value, str):
                encrypted_config[key] = {
                    "encrypted": True,
                    **self.service.encrypt_sensitive_data(
                        value,
                        additional_context={"config_key": key}
                    )
                }
            else:
                encrypted_config[key] = value
        
        return encrypted_config
    
    def decrypt_config(self, encrypted_config: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt configuration values"""
        
        decrypted_config = {}
        
        for key, value in encrypted_config.items():
            if isinstance(value, dict) and value.get("encrypted"):
                # Remove the encrypted flag and decrypt
                encryption_package = {k: v for k, v in value.items() if k != "encrypted"}
                decrypted_config[key] = self.service.decrypt_sensitive_data(encryption_package)
            else:
                decrypted_config[key] = value
        
        return decrypted_config
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a configuration key contains sensitive data"""
        
        key_lower = key.lower()
        return any(sensitive in key_lower for sensitive in self.sensitive_keys)