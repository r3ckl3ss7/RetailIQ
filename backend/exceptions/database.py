class DatabaseException(Exception):
    """Base class for database exceptions."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class DuplicateGSTNumberException(DatabaseException):
    """Raised when a business with the same GST number already exists."""
    pass


class DatabaseIntegrityException(DatabaseException):
    """Raised when database integrity constraints are violated."""
    pass


class DatabaseUnexpectedException(DatabaseException):
    """Raised when an unexpected database error occurs."""
    pass




class UserAlreadyExist(DatabaseException):
    """Raised when user email already exist"""


