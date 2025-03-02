from typing import Optional
import os
import structlog
import time

from PIL.Image import Image

from blackdog.display.adapters import DisplayAdapter
from blackdog.display.image import prepare_image


log_level = os.getenv("LOGLEVEL", "INFO").upper()
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)
log = structlog.get_logger()


class Orchestrator:

    def __init__(self, adapter: DisplayAdapter) -> None:
        self.adapter = adapter
        self.last_image = None
        self.capture_expires = 0

    def display(self, image: Image, gradient=True, capture: Optional[int]=None):
        if image == self.last_image:
            log.debug("orchestrator_display_dupe",
                      message="asked to display previously displayed image, ignoring",
                      image_len=len(image.tobytes()))
            return

        current_time = int(time.time())

        if capture:
            self.capture_expires = current_time + capture
            log.debug("orchestrator_display_captured",
                        current_time=current_time,
                        capture_expires=self.capture_expires)
        else:
            # this request is non-capturing, so we only proceed if capture has expired
            if current_time < self.capture_expires:
                log.debug("orchestrator_display_capture_not_expired",
                          message="asked to display non-capturing request, but capture not expired yet",
                          current_time=current_time,
                          capture_expires=self.capture_expires)
                return

        self.last_image = image
        output_image = prepare_image(self.adapter.get_output_size(),
                                     image, gradient)
        self.adapter.render(output_image)

