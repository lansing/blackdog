import io
import glob
import os
import random

from flask import Flask
from flask import request
from PIL import Image
from inky.inky_uc8159 import Inky
from colorthief import ColorThief
from colorthief import MMCQ


IMAGES_PARENT = os.environ.get('IMAGES_DIR', '/mnt/SDCARD/Images')


inky = Inky()
saturation = 0.8

app = Flask(__name__)

@app.route('/')
def home():
    return 'Display Server'


image_queue = []

def refill_image_queue():
    global image_queue
    subdirs = glob.glob(f"{IMAGES_PARENT}/*")
    subdirs.sort()
    current = subdirs[-1]
    image_queue = glob.glob(f"{current}/*")

def get_random_image():
    if len(image_queue) == 0:
        refill_image_queue()
    i = random.randint(0, len(image_queue)-1)
    image_path = image_queue.pop(i)
    print(f"\n\n got {len(image_queue)} left\n")
    f = open(image_path, 'rb')
    image_data = f.read()
    image = Image.open(io.BytesIO(image_data))
    return image


def get_color_edges(image):
    width = image.size[0]
    height = image.size[1]

    width_limit = int(width * 0.05)
    height_limit = int(height * 0.05)

    top = image.crop((0, 0, width, height_limit))
    left = image.crop((0,0, width_limit, height))
    right = image.crop((width - width_limit, 0, width, height))
    bottom = image.crop((0, height - height_limit, width, height))

    regions = (top, left, right, bottom)
    valid_pixels = []
    for region in regions:
        pixels = region.getdata()
        valid_pixels.extend(pixels)
    cmap = MMCQ.quantize(valid_pixels, 5)

    return cmap.palette[0]


def display_image(image):
    display_ratio = 600 / 448
    image_ratio = image.size[0] / image.size[1]

    if image_ratio > display_ratio:
      # fit to width
      new_width = 600
      new_height = new_width // image_ratio
    else:
      # fit to height
      new_height = 448
      new_width = new_height * image_ratio

    fit_image = image.resize((int(new_width), int(new_height)))

    bg_color = get_color_edges(fit_image)

    left = (600 - fit_image.size[0]) // 2
    top = (448 - fit_image.size[1]) // 2

    final_image = Image.new(image.mode, (600, 448), bg_color)
    final_image.paste(fit_image, (int(left), int(top)))

    inky.set_image(final_image, saturation=saturation)
    inky.show()



@app.route('/imagez', methods=['POST'])
def image():
    f = request.files['image']
    image_data = f.read()
    image = Image.open(io.BytesIO(image_data))

    #display_image(image)

    display_random_image()

    return "Done"


def display_random_image():
    image = get_random_image()
    display_image(image)


