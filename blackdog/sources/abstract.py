import io
import requests
import structlog
import os


log_level = os.getenv("LOGLEVEL", "INFO").upper()
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)
log = structlog.get_logger()


class Source:

    def __init__(self, display_url):
        self.display_url = display_url

    def display(self, image: bytes):
        log.debug(event="posting_to_display_server",
                  display_url=self.display_url,
                  source=self.__class__.__name__)
        try:
            requests.post(self.display_url,
                        files = {"image": io.BytesIO(image)})
        except Exception as e:
            log.exception(event="error_posting_display",
                          display_url=self.display_url,
                          source=self.__class__.__name__)


