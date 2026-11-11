class NewsUnavailableError(Exception):
    status_code = 503

    def __init__(self):
        super().__init__("News Unavailable")
