import os
from typing import Any, Dict
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/bizdesign")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    NOTIFICATION_QUEUE_URL: str = os.getenv("NOTIFICATION_QUEUE_URL", "redis://localhost:6379/1")
    
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External APIs
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Email
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    
    # Security & Encryption
    ENCRYPTION_MASTER_KEY: str = os.getenv("ENCRYPTION_MASTER_KEY", "")
    FIELD_ENCRYPTION_ENABLED: bool = os.getenv("FIELD_ENCRYPTION_ENABLED", "false").lower() == "true"
    
    # Rate Limiting
    RATE_LIMIT_STRATEGY: str = os.getenv("RATE_LIMIT_STRATEGY", "sliding_window")
    RATE_LIMIT_REDIS_DB: int = int(os.getenv("RATE_LIMIT_REDIS_DB", "2"))
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    
    # Data Retention
    DATA_RETENTION_DAYS: int = int(os.getenv("DATA_RETENTION_DAYS", "2555"))  # 7 years default
    AUDIT_LOG_RETENTION_DAYS: int = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "2555"))  # 7 years default
    EXPORT_FILE_RETENTION_DAYS: int = int(os.getenv("EXPORT_FILE_RETENTION_DAYS", "7"))
    
    # Other
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    def __init__(self):
        """Initialize settings and validate configuration"""
        
        self._validate_critical_settings()
        
        # Load encrypted configuration if available
        if self.FIELD_ENCRYPTION_ENABLED and not self.ENCRYPTION_MASTER_KEY:
            logger.warning("Field encryption enabled but no master key provided")
            self.FIELD_ENCRYPTION_ENABLED = False
    
    def _validate_critical_settings(self):
        """Validate critical configuration settings"""
        
        # Validate JWT secret in production
        if self.ENVIRONMENT == "production":
            if self.JWT_SECRET_KEY == "your-secret-key-here":
                raise ValueError("JWT_SECRET_KEY must be set in production")
            
            if len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
            
            if not self.ENCRYPTION_MASTER_KEY and self.FIELD_ENCRYPTION_ENABLED:
                raise ValueError("ENCRYPTION_MASTER_KEY must be set when field encryption is enabled")
    
    def get_secure_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary with sensitive values masked"""
        
        config = {}
        
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                # Mask sensitive values
                if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                    if value:
                        config[key] = f"***{'*' * (len(str(value)) - 6)}***" if len(str(value)) > 6 else "***"
                    else:
                        config[key] = "(not set)"
                else:
                    config[key] = value
        
        return config
    
    def get_encryption_config(self) -> Dict[str, Any]:
        """Get encryption-related configuration"""
        
        return {
            "field_encryption_enabled": self.FIELD_ENCRYPTION_ENABLED,
            "master_key_configured": bool(self.ENCRYPTION_MASTER_KEY),
            "environment": self.ENVIRONMENT
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security-related configuration"""
        
        return {
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "security_headers_enabled": self.SECURITY_HEADERS_ENABLED,
            "field_encryption_enabled": self.FIELD_ENCRYPTION_ENABLED,
            "rate_limit_strategy": self.RATE_LIMIT_STRATEGY,
            "jwt_algorithm": self.JWT_ALGORITHM,
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.REFRESH_TOKEN_EXPIRE_DAYS
        }
    
    def get_data_retention_config(self) -> Dict[str, Any]:
        """Get data retention configuration"""
        
        return {
            "data_retention_days": self.DATA_RETENTION_DAYS,
            "audit_log_retention_days": self.AUDIT_LOG_RETENTION_DAYS,
            "export_file_retention_days": self.EXPORT_FILE_RETENTION_DAYS
        }


# Singleton settings instance
settings = Settings()


# Configuration encryption utilities
def encrypt_config_file(config_path: str, output_path: str = None) -> str:
    """Encrypt a configuration file"""
    
    try:
        from app.services.encryption_service import ConfigurationEncryption
        
        config_encryption = ConfigurationEncryption()
        
        # Read configuration file
        with open(config_path, 'r') as f:
            import json
            config = json.load(f)
        
        # Encrypt sensitive values
        encrypted_config = config_encryption.encrypt_config(config)
        
        # Write encrypted configuration
        output_path = output_path or f"{config_path}.encrypted"
        with open(output_path, 'w') as f:
            json.dump(encrypted_config, f, indent=2)
        
        logger.info(f"Configuration encrypted and saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to encrypt configuration: {str(e)}")
        raise


def decrypt_config_file(encrypted_config_path: str, output_path: str = None) -> str:
    """Decrypt a configuration file"""
    
    try:
        from app.services.encryption_service import ConfigurationEncryption
        
        config_encryption = ConfigurationEncryption()
        
        # Read encrypted configuration
        with open(encrypted_config_path, 'r') as f:
            import json
            encrypted_config = json.load(f)
        
        # Decrypt sensitive values
        decrypted_config = config_encryption.decrypt_config(encrypted_config)
        
        # Write decrypted configuration
        output_path = output_path or f"{encrypted_config_path}.decrypted"
        with open(output_path, 'w') as f:
            json.dump(decrypted_config, f, indent=2)
        
        logger.info(f"Configuration decrypted and saved to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to decrypt configuration: {str(e)}")
        raise


# Environment-specific configuration validation
def validate_production_config():
    """Validate configuration for production deployment"""
    
    errors = []
    warnings = []
    
    # Check critical security settings
    if settings.DEBUG:
        errors.append("DEBUG must be False in production")
    
    if settings.JWT_SECRET_KEY == "your-secret-key-here":
        errors.append("JWT_SECRET_KEY must be changed from default value")
    
    if not settings.GEMINI_API_KEY:
        warnings.append("GEMINI_API_KEY is not set - AI features will not work")
    
    if not settings.SENDGRID_API_KEY:
        warnings.append("SENDGRID_API_KEY is not set - email notifications will not work")
    
    if settings.FIELD_ENCRYPTION_ENABLED and not settings.ENCRYPTION_MASTER_KEY:
        errors.append("ENCRYPTION_MASTER_KEY must be set when field encryption is enabled")
    
    # Check database URL
    if "localhost" in settings.DATABASE_URL and settings.ENVIRONMENT == "production":
        errors.append("DATABASE_URL should not use localhost in production")
    
    # Check Redis URL
    if "localhost" in settings.REDIS_URL and settings.ENVIRONMENT == "production":
        warnings.append("REDIS_URL uses localhost - ensure Redis is properly configured")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def get_config_summary() -> Dict[str, Any]:
    """Get a summary of current configuration"""
    
    return {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "security": settings.get_security_config(),
        "encryption": settings.get_encryption_config(),
        "data_retention": settings.get_data_retention_config(),
        "validation": validate_production_config() if settings.ENVIRONMENT == "production" else None
    }