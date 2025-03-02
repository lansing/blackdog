import io
import os
import structlog

from flask import Flask, request
from PIL import Image

from blackdog.display.orchestrator import Orchestrator

log_level = os.getenv("LOGLEVEL", "INFO").upper()
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)
log = structlog.get_logger()

app = Flask(__name__)

# TODO read a config file or env var to config adapter when we have more
try:
    from blackdog.display.adapters.inky import InkyExpression
    adapter = InkyExpression()
except ModuleNotFoundError as e:
    # We might be on a non-pi machine for dev
    log.warning(event="inky_no",
                message="Could not load inky, using LocalDisplay",
                error=str(e))
    from blackdog.display.adapters.local import LocalDisplay
    adapter = LocalDisplay()


orchestrator = Orchestrator(adapter)


app = Flask(__name__)


@app.route('/')
def home():
    return 'Display Server'


@app.route('/display', methods=['POST'])
def image():
    f = request.files['image']
    image_data = f.read()
    image = Image.open(io.BytesIO(image_data))

    gradient = (request.form.get('gradient') or '').lower() == 'true'
    capture = int(request.form.get('capture') or 0)

    log.debug(event="display_request",
              image_len=len(image_data),
              gradient=gradient,
              capture=capture)

    orchestrator.display(image, gradient, capture)

    return "displayed"

