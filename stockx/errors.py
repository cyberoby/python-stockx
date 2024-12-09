from collections.abc import Iterable
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .models import (
        BatchCreateResult,
        BatchUpdateResult,
        BatchDeleteResult,
    )
    from .ext.inventory import UpdateResult


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
    

class StockXBatchTimeout(StockXException):
    """Raised when a batch operation times out.

    Parameters
    ----------
    message : `str`
        Error message.
    queued_batch_ids : `Iterable[str]`
        Batch IDs that are still queued after timeout.
    partial_batch_results : `Iterable[BatchCreateResult | BatchUpdateResult | BatchDeleteResult]`
        Available results from completed batch operations.

    Attributes
    ----------
    message : `str`
    queued_batch_ids : `list[str]`
    partial_batch_results : `list[BatchCreateResult | BatchUpdateResult | BatchDeleteResult]`
    """
    def __init__(
            self, 
            message: str, 
            queued_batch_ids: Iterable[str],
            partial_batch_results: Iterable[
                BatchCreateResult | BatchUpdateResult | BatchDeleteResult
            ]
    ) -> None:
        super().__init__(message)
        self.message = message
        self.queued_batch_ids = list(queued_batch_ids)
        self.partial_batch_results = list(partial_batch_results)
    
    def __str__(self) -> str:
        return super().__str__() + f' Missing Batch IDs: {self.queued_batch_ids}'
    

class StockXIncompleteOperation(StockXException):
    """Raised when an operation couldn't complete fully.

    Parameters
    ----------
    message : `str`
        Error message.
    partial_results : `Iterable[UpdateResult]`
        Available results from completed operations.
    timed_out_batch_ids : `Iterable[str]`
        Batch IDs that are still queued after timeout.

    Attributes
    ----------
    message : `str`
    partial_results : `list[UpdateResult]`
    timed_out_batch_ids : `list[str]`
    """
    def __init__(
            self, 
            message: str,
            partial_results: Iterable[UpdateResult],
            timed_out_batch_ids: Iterable[str],
    ) -> None:
        super().__init__(message)
        self.message = message
        self.partial_results = list(partial_results)
        self.timed_out_batch_ids = list(timed_out_batch_ids)

    def __str__(self) -> str:
        return (
            f'{super().__str__()}\n'
            f'Incomplete batch IDs: {', '.join(self.timed_out_batch_ids)}\n'
            f'Completed results: {'\n'.join(str(r) for r in self.partial_results)}\n'
        )


class StockXOperationTimeout(StockXException):
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
    """Raised for HTTP 400 errors - invalid request."""
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
    """Raised for HTTP 429 errors - too many requests."""
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

