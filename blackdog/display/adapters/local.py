from blackdog.display.adapters import DisplayAdapter


class LocalDisplay(DisplayAdapter):
    
    def get_output_size(self):
        return (600, 448)

    def render(self, image):
        image.show()


