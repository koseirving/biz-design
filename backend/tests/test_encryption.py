import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.services.encryption_service import (
    DataEncryptionService,
    EncryptionMethod,
    EncryptionError,
    KeyManagementError
)


class TestDataEncryption:
    """Test data encryption functionality."""
    
    @pytest.fixture
    def encryption_service(self):
        """Create encryption service for testing."""
        with patch.dict(os.environ, {"ENCRYPTION_MASTER_KEY": "test-master-key-32-chars-long!!!"}):
            return DataEncryptionService()
    
    def test_aes_gcm_encryption_decryption(self, encryption_service):
        """Test AES-256-GCM encryption and decryption."""
        plaintext = "This is sensitive data that needs encryption"
        
        # Test encryption
        encrypted_result = encryption_service.encrypt_sensitive_data(
            data=plaintext,
            encryption_method=EncryptionMethod.AES_256_GCM
        )
        
        assert "encrypted_data" in encrypted_result
        assert "nonce" in encrypted_result
        assert "tag" in encrypted_result
        assert "method" in encrypted_result
        assert encrypted_result["method"] == EncryptionMethod.AES_256_GCM
        
        # Test decryption
        decrypted_data = encryption_service.decrypt_sensitive_data(encrypted_result)
        assert decrypted_data == plaintext
    
    def test_fernet_encryption_decryption(self, encryption_service):
        """Test Fernet encryption and decryption."""
        plaintext = "Fernet encrypted sensitive data"
        
        # Test encryption
        encrypted_result = encryption_service.encrypt_sensitive_data(
            data=plaintext,
            encryption_method=EncryptionMethod.FERNET
        )
        
        assert "encrypted_data" in encrypted_result
        assert "method" in encrypted_result
        assert encrypted_result["method"] == EncryptionMethod.FERNET
        
        # Test decryption
        decrypted_data = encryption_service.decrypt_sensitive_data(encrypted_result)
        assert decrypted_data == plaintext
    
    def test_rsa_encryption_decryption(self, encryption_service):
        """Test RSA-OAEP encryption and decryption."""
        plaintext = "RSA encrypted data"
        
        # Test encryption
        encrypted_result = encryption_service.encrypt_sensitive_data(
            data=plaintext,
            encryption_method=EncryptionMethod.RSA_OAEP
        )
        
        assert "encrypted_data" in encrypted_result
        assert "method" in encrypted_result
        assert encrypted_result["method"] == EncryptionMethod.RSA_OAEP
        
        # Test decryption
        decrypted_data = encryption_service.decrypt_sensitive_data(encrypted_result)
        assert decrypted_data == plaintext
    
    def test_hybrid_encryption_decryption(self, encryption_service):
        """Test hybrid encryption and decryption."""
        plaintext = "Hybrid encrypted large data content that exceeds RSA limits"
        
        # Test encryption
        encrypted_result = encryption_service.encrypt_sensitive_data(
            data=plaintext,
            encryption_method=EncryptionMethod.HYBRID
        )
        
        assert "encrypted_data" in encrypted_result
        assert "encrypted_key" in encrypted_result
        assert "nonce" in encrypted_result
        assert "tag" in encrypted_result
        assert "method" in encrypted_result
        assert encrypted_result["method"] == EncryptionMethod.HYBRID
        
        # Test decryption
        decrypted_data = encryption_service.decrypt_sensitive_data(encrypted_result)
        assert decrypted_data == plaintext
    
    def test_dict_encryption_decryption(self, encryption_service):
        """Test dictionary encryption and decryption."""
        data_dict = {
            "username": "testuser",
            "email": "test@example.com",
            "sensitive_data": "very secret information"
        }
        
        # Test encryption
        encrypted_result = encryption_service.encrypt_sensitive_data(
            data=data_dict,
            encryption_method=EncryptionMethod.AES_256_GCM
        )
        
        assert "encrypted_data" in encrypted_result
        assert "method" in encrypted_result
        
        # Test decryption
        decrypted_data = encryption_service.decrypt_sensitive_data(encrypted_result)
        assert decrypted_data == data_dict
    
    def test_bytes_encryption_decryption(self, encryption_service):
        """Test bytes encryption and decryption."""
        data_bytes = b"Binary data that needs encryption"
        
        # Test encryption
        encrypted_result = encryption_service.encrypt_sensitive_data(
            data=data_bytes,
            encryption_method=EncryptionMethod.AES_256_GCM
        )
        
        assert "encrypted_data" in encrypted_result
        
        # Test decryption
        decrypted_data = encryption_service.decrypt_sensitive_data(encrypted_result)
        assert decrypted_data == data_bytes
    
    def test_field_level_encryption(self, encryption_service):
        """Test field-level encryption functionality."""
        fields_to_encrypt = ["password", "credit_card", "ssn"]
        data = {
            "username": "testuser",
            "password": "secretpassword",
            "credit_card": "1234-5678-9012-3456",
            "ssn": "123-45-6789",
            "public_info": "This can be visible"
        }
        
        # Test field encryption
        encrypted_data = encryption_service.encrypt_fields(
            data=data,
            fields_to_encrypt=fields_to_encrypt
        )
        
        # Check that specified fields are encrypted
        for field in fields_to_encrypt:
            assert isinstance(encrypted_data[field], dict)
            assert "encrypted_data" in encrypted_data[field]
            assert "method" in encrypted_data[field]
        
        # Check that non-specified fields remain unchanged
        assert encrypted_data["username"] == data["username"]
        assert encrypted_data["public_info"] == data["public_info"]
        
        # Test field decryption
        decrypted_data = encryption_service.decrypt_fields(encrypted_data, fields_to_encrypt)
        assert decrypted_data == data
    
    def test_key_derivation(self, encryption_service):
        """Test key derivation functionality."""
        password = "test-password"
        salt = os.urandom(16)
        
        # Test key derivation
        derived_key = encryption_service._derive_key(password, salt)
        
        assert len(derived_key) == 32  # 256-bit key
        
        # Test that same inputs produce same key
        derived_key2 = encryption_service._derive_key(password, salt)
        assert derived_key == derived_key2
        
        # Test that different salts produce different keys
        different_salt = os.urandom(16)
        different_key = encryption_service._derive_key(password, different_salt)
        assert derived_key != different_key
    
    def test_key_rotation_support(self, encryption_service):
        """Test key rotation functionality."""
        plaintext = "Data to be re-encrypted with new key"
        
        # Encrypt with current key
        encrypted_v1 = encryption_service.encrypt_sensitive_data(
            data=plaintext,
            encryption_method=EncryptionMethod.AES_256_GCM
        )
        
        # Simulate key rotation
        with patch.object(encryption_service, '_get_current_key_version', return_value=2):
            # Encrypt same data with "new" key
            encrypted_v2 = encryption_service.encrypt_sensitive_data(
                data=plaintext,
                encryption_method=EncryptionMethod.AES_256_GCM
            )
        
        # Both should decrypt to same plaintext
        decrypted_v1 = encryption_service.decrypt_sensitive_data(encrypted_v1)
        decrypted_v2 = encryption_service.decrypt_sensitive_data(encrypted_v2)
        
        assert decrypted_v1 == plaintext
        assert decrypted_v2 == plaintext
    
    def test_invalid_encryption_method(self, encryption_service):
        """Test handling of invalid encryption method."""
        with pytest.raises(EncryptionError):
            encryption_service.encrypt_sensitive_data(
                data="test",
                encryption_method="invalid_method"
            )
    
    def test_decrypt_invalid_data(self, encryption_service):
        """Test decryption of invalid/corrupted data."""
        invalid_encrypted_data = {
            "encrypted_data": "invalid_base64_data",
            "method": EncryptionMethod.AES_256_GCM,
            "nonce": "invalid_nonce"
        }
        
        with pytest.raises(EncryptionError):
            encryption_service.decrypt_sensitive_data(invalid_encrypted_data)
    
    def test_missing_master_key(self):
        """Test service behavior without master key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(KeyManagementError):
                DataEncryptionService()
    
    @patch('app.services.encryption_service.secretmanager')
    def test_gcp_secret_manager_integration(self, mock_secretmanager):
        """Test GCP Secret Manager integration."""
        # Mock Secret Manager client
        mock_client = Mock()
        mock_secretmanager.SecretManagerServiceClient.return_value = mock_client
        
        # Mock secret access
        mock_response = Mock()
        mock_response.payload.data = b"secret-key-from-gcp"
        mock_client.access_secret_version.return_value = mock_response
        
        # Test key retrieval
        service = DataEncryptionService()
        key = service._get_key_from_secret_manager("test-secret-name")
        
        assert key == b"secret-key-from-gcp"
        mock_client.access_secret_version.assert_called_once()
    
    def test_encryption_performance(self, encryption_service):
        """Test encryption performance with different data sizes."""
        import time
        
        # Test different data sizes
        test_sizes = [100, 1000, 10000, 100000]  # bytes
        
        for size in test_sizes:
            data = "x" * size
            
            start_time = time.time()
            encrypted = encryption_service.encrypt_sensitive_data(
                data=data,
                encryption_method=EncryptionMethod.AES_256_GCM
            )
            encryption_time = time.time() - start_time
            
            start_time = time.time()
            decrypted = encryption_service.decrypt_sensitive_data(encrypted)
            decryption_time = time.time() - start_time
            
            # Verify correctness
            assert decrypted == data
            
            # Performance should be reasonable (less than 1 second for 100KB)
            if size <= 100000:
                assert encryption_time < 1.0
                assert decryption_time < 1.0


class TestEncryptionUtilities:
    """Test encryption utility functions."""
    
    def test_generate_secure_key(self):
        """Test secure key generation."""
        from app.services.encryption_service import generate_secure_key
        
        key1 = generate_secure_key()
        key2 = generate_secure_key()
        
        # Keys should be different
        assert key1 != key2
        
        # Keys should be proper length (32 bytes for AES-256)
        assert len(key1) == 32
        assert len(key2) == 32
    
    def test_validate_encryption_config(self):
        """Test encryption configuration validation."""
        from app.services.encryption_service import validate_encryption_config
        
        # Valid config
        valid_config = {
            "master_key": "a" * 32,
            "field_encryption_enabled": True,
            "supported_methods": ["aes_256_gcm", "fernet"]
        }
        assert validate_encryption_config(valid_config) is True
        
        # Invalid config - missing master key
        invalid_config = {
            "field_encryption_enabled": True
        }
        assert validate_encryption_config(invalid_config) is False
    
    def test_encryption_metadata(self, encryption_service):
        """Test encryption metadata handling."""
        data = "test data"
        
        encrypted = encryption_service.encrypt_sensitive_data(
            data=data,
            encryption_method=EncryptionMethod.AES_256_GCM
        )
        
        # Check metadata
        assert "timestamp" in encrypted
        assert "key_version" in encrypted
        assert "method" in encrypted
        
        # Validate timestamp format
        from datetime import datetime
        timestamp = datetime.fromisoformat(encrypted["timestamp"])
        assert timestamp is not None
    
    def test_bulk_encryption(self, encryption_service):
        """Test bulk encryption operations."""
        data_list = [
            "sensitive data 1",
            "sensitive data 2", 
            "sensitive data 3"
        ]
        
        # Test bulk encryption
        encrypted_list = encryption_service.encrypt_bulk(
            data_list=data_list,
            encryption_method=EncryptionMethod.AES_256_GCM
        )
        
        assert len(encrypted_list) == len(data_list)
        
        # Test bulk decryption
        decrypted_list = encryption_service.decrypt_bulk(encrypted_list)
        
        assert decrypted_list == data_list
    
    def test_encryption_audit_logging(self, encryption_service):
        """Test that encryption operations are audited."""
        with patch('app.services.audit_log_service.audit_logger') as mock_audit:
            data = "sensitive data"
            
            # Encrypt data
            encrypted = encryption_service.encrypt_sensitive_data(
                data=data,
                encryption_method=EncryptionMethod.AES_256_GCM
            )
            
            # Verify audit logging
            mock_audit.log_event.assert_called()
            
            # Check audit log content
            call_args = mock_audit.log_event.call_args
            assert "encryption_operation" in str(call_args)


class TestEncryptionEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_data_encryption(self, encryption_service):
        """Test encryption of empty data."""
        empty_string = ""
        empty_bytes = b""
        empty_dict = {}
        
        # Should handle empty data gracefully
        for empty_data in [empty_string, empty_bytes, empty_dict]:
            encrypted = encryption_service.encrypt_sensitive_data(
                data=empty_data,
                encryption_method=EncryptionMethod.AES_256_GCM
            )
            decrypted = encryption_service.decrypt_sensitive_data(encrypted)
            assert decrypted == empty_data
    
    def test_very_large_data_encryption(self, encryption_service):
        """Test encryption of very large data."""
        # 1MB of data
        large_data = "x" * (1024 * 1024)
        
        # Should use hybrid encryption for large data
        encrypted = encryption_service.encrypt_sensitive_data(
            data=large_data,
            encryption_method=EncryptionMethod.HYBRID
        )
        
        assert encrypted["method"] == EncryptionMethod.HYBRID
        
        decrypted = encryption_service.decrypt_sensitive_data(encrypted)
        assert decrypted == large_data
    
    def test_unicode_data_encryption(self, encryption_service):
        """Test encryption of unicode data."""
        unicode_data = "测试数据 🔐 émoji dáta"
        
        encrypted = encryption_service.encrypt_sensitive_data(
            data=unicode_data,
            encryption_method=EncryptionMethod.AES_256_GCM
        )
        
        decrypted = encryption_service.decrypt_sensitive_data(encrypted)
        assert decrypted == unicode_data
    
    def test_nested_dict_encryption(self, encryption_service):
        """Test encryption of nested dictionaries."""
        nested_data = {
            "user": {
                "profile": {
                    "sensitive_info": "secret data",
                    "public_info": "public data"
                }
            },
            "settings": {
                "password": "secret_password"
            }
        }
        
        encrypted = encryption_service.encrypt_sensitive_data(
            data=nested_data,
            encryption_method=EncryptionMethod.AES_256_GCM
        )
        
        decrypted = encryption_service.decrypt_sensitive_data(encrypted)
        assert decrypted == nested_data