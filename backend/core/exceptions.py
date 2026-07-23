

class DatabaseOperationError(Exception):
    """Raised when a database operation cannot be completed."""


class RateLimitExceededError(Exception):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")


class MetricsAccessDeniedError(Exception):
    """Raised when access to protected metrics is denied."""
