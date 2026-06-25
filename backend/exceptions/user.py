class UserException(Exception):
    """Base exception for user-related errors."""
    def __init__(self, message: str, status_code: int, error_code: str):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class EmailAlreadyRegisteredException(UserException):
    """Raised when trying to register with an email that already exists."""
    def __init__(self, message: str = "Email already registered"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="EMAIL_ALREADY_REGISTERED"
        )


class ProfileModificationForbiddenException(UserException):
    """Raised when a user tries to modify a profile they don't own."""
    def __init__(self, message: str = "You are not allowed to modify this profile"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="PROFILE_MODIFICATION_FORBIDDEN"
        )


class UserNotFoundException(UserException):
    """Raised when a user is not found."""
    def __init__(self, message: str = "User not found"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="USER_NOT_FOUND"
        )


class EmailAlreadyInUseException(UserException):
    """Raised when updating a profile to an email that is already used by another user."""
    def __init__(self, message: str = "Email already in use"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="EMAIL_ALREADY_IN_USE"
        )




class UserDeletionForbiddenException(UserException):
    """Raised when a user tries to delete a profile they don't own."""
    def __init__(self, message: str = "You are not allowed to delete this user"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="USER_DELETION_FORBIDDEN"
        )

