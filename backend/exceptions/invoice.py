class InvoiceException(Exception):
    """Base class for all invoice exceptions."""
    def __init__(self, message: str, status_code: int, error_code: str):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class InvoiceNotFoundException(InvoiceException):
    def __init__(self, message: str = "Invoice not found"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="INVOICE_NOT_FOUND"
        )


class InvalidInvoiceException(InvoiceException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code="INVALID_INVOICE"
        )


class InsufficientStockException(InvoiceException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code="INSUFFICIENT_STOCK"
        )
