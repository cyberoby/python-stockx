from collections.abc import Iterable
from typing import Literal


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
            status_code: Literal[400] = 400
    ) -> None:
        super().__init__(message, status_code)


class StockXUnauthorized(StockXRequestError):
    """Raised for HTTP 401 errors - authentication issues."""
    def __init__(
            self, 
            message: str = 'Unauthorized access.',
            status_code: Literal[401] = 401
    ) -> None:
        super().__init__(message, status_code)


class StockXForbidden(StockXRequestError):
    """Raised for HTTP 403 errors - insufficient permissions."""
    def __init__(
            self, 
            message: str = 'Forbidden.',
            status_code: Literal[403] = 403
    ) -> None:
        super().__init__(message, status_code)


class StockXNotFound(StockXRequestError):
    """Raised for HTTP 404 errors - resource not found."""
    def __init__(
            self, 
            message: str = 'Resource not found.', 
            status_code: Literal[404] = 404
    ) -> None:
        super().__init__(message, status_code)


class StockXRateLimited(StockXRequestError):
    """Raised for HTTP 429 errors - rate limited."""
    def __init__(
            self, 
            message: str = "You're going too fast.", 
            status_code: Literal[429] = 429
    ) -> None:
        super().__init__(message, status_code)


class StockXInternalServerError(StockXRequestError):
    """Raised for HTTP 500 errors - server-side issues."""
    def __init__(
            self, 
            message: str = 'Internal server error.', 
            status_code: Literal[500] = 500
    ) -> None:
        super().__init__(message, status_code)


class StockXRequestTooLarge(StockXRequestError):
    """Raised for HTTP 413 errors - request payload too large."""
    def __init__(
            self, 
            message: str = 'Request payload too large.', 
            status_code: Literal[413] = 413
    ) -> None:
        super().__init__(message, status_code)


class StockXUnsupportedMediaType(StockXRequestError):
    """Raised for HTTP 415 errors - unsupported media type."""
    def __init__(
            self, 
            message: str = 'Unsupported media type.', 
            status_code: Literal[415] = 415
    ) -> None:
        super().__init__(message, status_code)


class StockXServiceUnavailable(StockXRequestError):
    """Raised for HTTP 503 errors - service unavailable."""
    def __init__(
            self, 
            message: str = 'Service temporarily unavailable.', 
            status_code: Literal[503] = 503
    ) -> None:
        super().__init__(message, status_code)


class StockXGatewayTimeout(StockXRequestError):
    """Raised for HTTP 504 errors - gateway timeout."""
    def __init__(
            self, 
            message: str = 'Gateway timeout.', 
            status_code: Literal[504] = 504
    ) -> None:
        super().__init__(message, status_code)


def stockx_request_error(
        message: str, 
        status_code: int | None = None
) -> StockXRequestError:
    """
    Create appropriate StockXRequestError subclass based on HTTP status code.

    Parameters
    ----------
    message : str
        Error message to include in the exception.
    status_code : int | None
        HTTP status code that triggered the error.

    Returns
    -------
    StockXRequestError
        Appropriate exception subclass for the status code.
    """
    config = {
        400: StockXBadRequest,
        401: StockXUnauthorized,
        403: StockXForbidden,
        404: StockXNotFound,
        413: StockXRequestTooLarge,
        415: StockXUnsupportedMediaType,
        429: StockXRateLimited,
        500: StockXInternalServerError,
        503: StockXServiceUnavailable,
        504: StockXGatewayTimeout,
    }
    try:
        return config[status_code](message, status_code)
    except KeyError:
        return StockXRequestError(message, status_code)

