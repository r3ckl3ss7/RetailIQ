class ProductException(Exception):
    """Base class for all Product exceptions."""
    def __init__(self, message: str, status_code: int, error_code: str):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class ProductNotFound(ProductException):
    def __init__(self, message: str = "Product not found"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="PRODUCT_NOT_FOUND"
        )