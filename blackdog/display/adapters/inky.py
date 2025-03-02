from inky.inky_uc8159 import Inky

from blackdog.display.adapters import DisplayAdapter


class InkyExpression(DisplayAdapter):

    SATURATION = 0.6

    def __init__(self) -> None:
        self.inky = Inky()

    def get_output_size(self):
        return (600, 448)
    
    def render(self, image):
        self.inky.set_image(image, saturation=self.SATURATION)
        self.inky.show()

        
