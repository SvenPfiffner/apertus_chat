from typing import Optional

class ApertusAPIError(Exception):
    """Raised when the Apertus API returns a non-success HTTP status."""

    def __init__(self, status_code: int, message: str, *, url: Optional[str] = None, payload: Optional[dict] = None):
        super().__init__(f"Apertus API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.url = url
        self.payload = payload
