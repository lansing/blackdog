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

    def display(self, image: bytes, gradient=True, capture=3600):
        data = {
            'gradient': gradient,
            'capture': capture
        }
        log.debug(event="posting_to_display_server",
                  display_url=self.display_url,
                  data=data,
                  image_len=len(image),
                  source=self.__class__.__name__)
        try:
            response = requests.post(self.display_url,
                                     data=data,
                                     files={"image": io.BytesIO(image)})
            response.raise_for_status()
        except Exception as e:
            log.exception(event="error_posting_display",
                          display_url=self.display_url,
                          image_len=len(image),
                          source=self.__class__.__name__)


    def run(self):
        raise NotImplementedError("Implement in subclass")

