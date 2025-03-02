from typing import Optional

from PIL.Image import Image

from blackdog.display.adapters import DisplayAdapter
from blackdog.display.image import prepare_image


class Orchestrator:

    def __init__(self, adapter: DisplayAdapter) -> None:
        self.adapter = adapter

    def display(self, image: Image, gradient=True, capture: Optional[int]=None):
        # TODO implement capture...
        # record capture expiration time
        # if a non-capture is sent and expiration has not been reached, then ignore
        
        output_image = prepare_image(self.adapter.get_output_size(),
                                     image, gradient)
        self.adapter.render(output_image)

