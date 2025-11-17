# common/exceptions.py

from typing import Dict, Any

class ApplicationError(Exception):
    """
    Base exception class for the application.
    All custom exceptions should inherit from this class.
    """
    def __init__(self: 'ApplicationError', message: str) -> None:
        self.message: str = message
        super().__init__(self.message)

class NotFoundError(ApplicationError):
    """
    Raised when a requested resource is not found in the system.
    Corresponds to an HTTP 404 Not Found response.
    """
    pass

class ValidationError(ApplicationError):
    """
    Raised when input data fails validation checks.
    Corresponds to an HTTP 400 Bad Request response.
    It can hold a dictionary of field-specific errors.
    """
    def __init__(self: 'ValidationError', errors: Dict[str, Any]) -> None:
        self.errors: Dict[str, Any] = errors
        # Create a user-friendly message from the errors dictionary
        super().__init__("Input validation failed")

class ConflictError(ApplicationError):
    """
    Raised when an action cannot be completed because of a conflict
    with the current state of the resource.
    E.g., trying to create an item that already exists.
    Corresponds to an HTTP 409 Conflict response.
    """
    pass

class UnauthorizedError(ApplicationError):
    """
    Raised for authorization failures, e.g., a user trying to access
    a resource they do not have permission to view.
    Corresponds to an HTTP 403 Forbidden response.
    """
    pass
