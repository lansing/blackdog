class DisplayAdapter:

    def get_output_size(self):
        raise NotImplementedError("Must implement in subclass")

    def render(self, image):
        raise NotImplementedError("Must implement in subclass")

