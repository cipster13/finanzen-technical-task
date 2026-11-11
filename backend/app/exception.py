class ServiceUnavailableError(Exception):
    status_code = 503


class NewsUnavailableError(ServiceUnavailableError):
    def __init__(self, ticker: str):
        super().__init__(f"News unavailable for {ticker}")


class SummaryUnavailableError(ServiceUnavailableError):
    def __init__(self):
        super().__init__("Summary unavailable")
