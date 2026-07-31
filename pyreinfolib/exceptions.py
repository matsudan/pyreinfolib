"""Exceptions raised by pyreinfolib.

Every error raised by this library derives from `ReinfolibError`, so a caller can guard
a call site without importing `requests`. That keeps the transport an implementation
detail: swapping it out later does not change the exceptions callers catch.

This module deliberately imports nothing from `requests`. Translating a response into
one of these exceptions is the client's job, in `pyreinfolib.client`.
"""


class ReinfolibError(Exception):
    """Base class for every error raised by this library."""


class TransportError(ReinfolibError):
    """No response was obtained from the API.

    Raised for connection failures, DNS errors and timeouts. There is no status code to
    inspect; the underlying transport exception is kept as `__cause__`.
    """


class APIError(ReinfolibError):
    """The API responded, but the response could not be used.

    :ivar status_code: HTTP status code of the response.
    :ivar response_body: Raw response body. The API explains itself here, usually as
      `{"message": ...}`.
    :ivar url: The requested URL. The API key travels in a header, not the query string,
      so this is safe to log.
    """

    def __init__(self, message: str, *, status_code: int, response_body: str, url: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.url = url


class AuthenticationError(APIError):
    """The API key was missing or rejected (HTTP 401)."""


class NoResultsError(APIError):
    """The query matched no data (HTTP 404).

    This is a normal outcome, not a fault. The three endpoints that do not take tile
    coordinates -- XIT001, XIT002 and XCT001 -- answer 404 instead of returning an empty
    result set. Endpoints that do take tile coordinates answer 200 with an empty feature
    list, and so never raise this.

    See section 3, Q.8 of https://www.reinfolib.mlit.go.jp/help/apiManual/
    """


class RateLimitError(APIError):
    """The API key sent too many requests in too short a period (HTTP 429).

    The API publishes no explicit request ceiling; it asks that calls be spaced out.
    See section 3, Q.3 of https://www.reinfolib.mlit.go.jp/help/apiManual/
    """


class InvalidResponseError(APIError):
    """The response body was not the JSON the API is documented to return.

    A maintenance page served with HTTP 200 lands here, which is why this carries a
    status code like the other `APIError` subclasses.
    """
