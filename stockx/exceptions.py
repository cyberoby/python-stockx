from collections.abc import Iterable


class StockXException(Exception):
    """Base exception class for StockX."""
    def __str__(self) -> str:
        return f'{self.__class__.__name__}: {self.args[0]}'


class StockXNotInitialized(StockXException):
    """Raised when a request is sent before the client is initialized.""" 
    def __init__(
            self, 
            message: str = 'Client must be initialized before making requests.'
    ) -> None:
        super().__init__(message)
    

class StockXBatchTimeout(Exception):
    """Raised when a batch operation times out."""
    def __init__(
            self, 
            message: str, 
            batch_ids: Iterable[str],
    ) -> None:
        super().__init__(message)
        self.message = message
        self.batch_ids = batch_ids

    def __str__(self) -> str:
        return super().__str__() + f' Missing Batch IDs: {self.batch_ids}'


class StockXOperationTimeout(Exception):
    """Raised when an operation times out."""
    def __init__(
            self, 
            message: str, 
            operation_id: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.operation_id = operation_id

    def __str__(self) -> str:
        return super().__str__() + f' Operation ID: {self.operation_id}'
    

class StockXRequestError(StockXException):
    """Raised for errors occurring during HTTP requests."""
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        if self.status_code:
            return super().__str__() + f' (Status Code: {self.status_code})'
        return super().__str__()
    

class StockXBadRequest(StockXRequestError):
    """Raised for HTTP 400 errors - invalid requests."""
    def __init__(
            self, 
            message: str = 'Bad request.', 
            status_code: int = 400
    ) -> None:
        super().__init__(message, status_code)


class StockXUnauthorized(StockXRequestError):
    """Raised for HTTP 401 errors - authentication issues."""
    def __init__(
            self, 
            message: str = 'Unauthorized access.',
            status_code: int = 401
    ) -> None:
        super().__init__(message, status_code)


class StockXForbidden(StockXRequestError):
    """Raised for HTTP 403 errors - insufficient permissions."""
    def __init__(
            self, 
            message: str = 'Forbidden.',
            status_code: int = 403
    ) -> None:
        super().__init__(message, status_code)


class StockXNotFound(StockXRequestError):
    """Raised for HTTP 404 errors - resource not found."""
    def __init__(
            self, 
            message: str = 'Resource not found.', 
            status_code: int = 404
    ) -> None:
        super().__init__(message, status_code)


class StockXRateLimited(StockXRequestError):
    """Raised for HTTP 429 errors - rate limited."""
    def __init__(
            self, 
            message: str = "You're going too fast.", 
            status_code: int = 429
    ) -> None:
        super().__init__(message, status_code)


class StockXInternalServerError(StockXRequestError):
    """Raised for HTTP 500 errors - server-side issues."""
    def __init__(
            self, 
            message: str = 'Internal server error.', 
            status_code: int = 500
    ) -> None:
        super().__init__(message, status_code)


def stockx_request_error(message, status_code = None):
    config = {
        400: StockXBadRequest,
        401: StockXUnauthorized,
        403: StockXForbidden,
        404: StockXNotFound,
        429: StockXRateLimited,
        500: StockXInternalServerError,
    }
    try:
        return config[status_code](message, status_code)
    except KeyError:
        return StockXRequestError(message, status_code)

