import io
import glob
import os
import random
from threading import Event, Thread

import numpy as np

from flask import Flask
from flask import request
from PIL import Image
from inky.inky_uc8159 import Inky
from colorthief import ColorThief
from colorthief import MMCQ


SCREEN_SAVER_WAIT = 60*60*2
SCREEN_SAVER_REFRESH = 60*60

IMAGES_PARENT = os.environ.get('IMAGES_DIR', '/mnt/SDCARD/Images')


inky = Inky()
saturation = 0.6

WIDTH = 600
HEIGHT = 448
CORNER_LIMIT = 0.2


class ScreenSaverThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        wait = SCREEN_SAVER_WAIT
        while not self.stopped.wait(wait):
            display_random_image()
            wait = SCREEN_SAVER_REFRESH

class ScreenSaver():
    def __init__(self):
        self.stop_flag = Event()

    def start(self):
        ScreenSaverThread(self.stop_flag).start()

    def reset(self):
        self.stop_flag.set()
        self.stop_flag = Event()
        self.start()


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
    f = open(image_path, 'rb')
    image_data = f.read()
    image = Image.open(io.BytesIO(image_data))
    return image


def get_bg_color(image):
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


def get_corners(image_size):
    limit = CORNER_LIMIT
    width = image_size[0]
    height = image_size[1]
    width_limit = int(width * limit)
    height_limit = int(height * limit)
    topleft = (0, 0, width_limit, height_limit)
    topright = (width-width_limit,0, width, height_limit)
    bottomright = (width - width_limit, height-height_limit, width, height)
    bottomleft = (0, height - height_limit, width_limit, height)
    return (topleft, topright, bottomright, bottomleft)


def get_colors_corners(image):
    corners = get_corners(image.size)
    corner_colors = []
    for corner in corners:
        region = image.crop(corner)
        pixels = region.getdata()
        cmap = MMCQ.quantize(pixels, 5)
        color = cmap.palette[0]
        corner_colors.append(color)
    return corner_colors


def draw_gradient_bg(size, colors):
    """colors needs to be [topLeft, topRight, bottomRight, bottomLeft]"""
    w = size[0]
    h = size[1]
    pix_indices = np.indices((w,h)).T
    # create mask for top-left color, then mirror it to get additional masks
    tl_mask = ((w-1,h-1) - pix_indices) / (w-1,h-1)  # top left is 1,1
    tl_mask_c = np.repeat(tl_mask, 3).reshape((h,w,2,3))  # repeat for 3 channels
    mirrors = [(0,0), (1,0), (1,1), (0,1)]
    img = np.zeros((h, w, 3))
    for i in range(len(mirrors)):
        mirror_x, mirror_y = mirrors[i]
        x_mult, y_mult, x_add, y_add = (1-mirror_x*2), (1-mirror_y*2), mirror_x, mirror_y
        mask_mirrored = tl_mask_c * ((x_mult,),(y_mult,)) + ((x_add,),(y_add,))
        mask_mirrored_combined = mask_mirrored[:,:,0] * mask_mirrored[:,:,1]
        img += mask_mirrored_combined * colors[i]
    return Image.fromarray(np.uint8(img))


# For debug only
# in_image = Image.open(io.BytesIO(open("/Users/max/Desktop/700138.jpg", "rb").read()))
# cor = get_colors_corners(in_image)
# image = draw_gradient_bg((600,448), cor)
# image.save("/Users/max/Desktop/image.png")


def display_image(image, gradient=True):
    display_ratio = WIDTH / HEIGHT
    image_ratio = image.size[0] / image.size[1]

    if image_ratio > display_ratio:
      # fit to width
      new_width = WIDTH
      new_height = new_width // image_ratio
    else:
      # fit to height
      new_height = HEIGHT
      new_width = new_height * image_ratio

    fit_image = image.resize((int(new_width), int(new_height)))

    left = (WIDTH - fit_image.size[0]) // 2
    top = (HEIGHT - fit_image.size[1]) // 2

    if gradient:
            corner_colors = get_colors_corners(fit_image)
    else:
            corner_colors = [(255,255,255)]*4

    final_image = draw_gradient_bg((WIDTH, HEIGHT), corner_colors)
    final_image.paste(fit_image, (int(left), int(top)))

    inky.set_image(final_image, saturation=saturation)
    inky.show()


screen_saver = None

def reset_screen_saver():
    global screen_saver

    if not screen_saver:
        screen_saver = ScreenSaver()
        screen_saver.start()
    else:
        screen_saver.reset()


@app.route('/imagez', methods=['POST'])
def image():
    reset_screen_saver()

    f = request.files['image']
    image_data = f.read()
    image = Image.open(io.BytesIO(image_data))

    display_image(image)

    return "displayed"

@app.route('/start_screen_saver', methods=['POST'])
def start_screen_saver():
    reset_screen_saver()
    display_random_image()
    return "displayed"


def display_random_image():
    image = get_random_image()
    display_image(image, gradient=False)

