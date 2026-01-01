"""
Custom exceptions for the drift-sre library
"""


class DriftError(Exception):
    """Base exception for all drift-sre errors"""
    pass


class ConfigurationError(DriftError):
    """Raised when there's an error in configuration"""
    pass


class NotificationError(DriftError):
    """Raised when notification sending fails"""
    pass

