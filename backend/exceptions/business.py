class BusinessException(Exception):

    def __init__(self, error_code: str, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = message


class DuplicateGSTNumber(BusinessException):
    def __init__(self, message: str = "Business with this GST number already exists"):
        super().__init__(
            "DUPLICATE_GST_NUMBER",
            message,
            400
        )


class BusinessNotFoundException(BusinessException):
    def __init__(self, message: str = "Business not found"):
        super().__init__(
            "BUSINESS_NOT_FOUND",
            message,
            404
        )


class BusinessModificationForbiddenException(BusinessException):
    def __init__(self, message: str = "You are not allowed to modify this business"):
        super().__init__(
            "BUSINESS_MODIFICATION_FORBIDDEN",
            message,
            403
        )




class BusinessDeletionForbiddenException(BusinessException):
    def __init__(self, message: str = "You are not allowed to delete this business"):
        super().__init__(
            "BUSINESS_DELETION_FORBIDDEN",
            message,
            403
        )
