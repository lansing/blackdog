from colorthief import MMCQ
from PIL import Image
import numpy as np


CORNER_BUFFER = 0.2 # how much of the image to consider per corner, for color extraction
NEUTRAL_BG_COLOR = (255, 255, 255)


def get_corners(image_size):
    """
    get corner regions for a rect
    """
    limit = CORNER_BUFFER
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
    """
    get quantized primary color for each corner in an image
    """
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
    """
    colors needs to be [topLeft, topRight, bottomRight, bottomLeft]

    draws a four-corner gradient on a rectangle.

    given a rect dimensions, and four colors (one for each corner),
    will gradient-ify the rectangle.

    i.e. the pixel in each corner will be the full value of the
    respective color, and every other pixel will be a weighted
    average of the colors, weighted by the pixel's distance from
    each color's corner.
    """
    w = size[0]
    h = size[1]
    pix_indices = np.indices((w,h)).T
    # create mask for top-left color
    tl_mask = ((w-1,h-1) - pix_indices) / (w-1,h-1)  # top left is 1,1
    tl_mask_c = np.repeat(tl_mask, 3).reshape((h,w,2,3))  # repeat for 3 channels
    # mirror it both axes for all four corners (1 will flip the original, 0 keeps it the same)
    mirrors = [(0,0), (1,0), (1,1), (0,1)]
    img = np.zeros((h, w, 3))
    for i in range(len(mirrors)):
        mirror_x, mirror_y = mirrors[i]
        x_mult, y_mult, x_add, y_add = (1-mirror_x*2), (1-mirror_y*2), mirror_x, mirror_y
        mask_mirrored = tl_mask_c * ((x_mult,),(y_mult,)) + ((x_add,),(y_add,))
        mask_mirrored_combined = mask_mirrored[:,:,0] * mask_mirrored[:,:,1]
        img += mask_mirrored_combined * colors[i]
    return Image.fromarray(np.uint8(img))


def prepare_image(size, image, gradient=True):
    """
    Draws an image into a the center of a rect (smartly pad either height or width)
    if gradient=True, then we will fill the bg with a smart four-corner gradient
    using the primary color in each corner.
    otherwise, just fill the bg with a neutral color.
    """
    width, height = size
    display_ratio = width / height
    image_ratio = image.size[0] / image.size[1]

    if image_ratio > display_ratio:
      # fit to width
      new_width = width 
      new_height = new_width // image_ratio
    else:
      # fit to height
      new_height = height 
      new_width = new_height * image_ratio

    fit_image = image.resize((int(new_width), int(new_height)))

    left = (width - fit_image.size[0]) // 2
    top = (height - fit_image.size[1]) // 2

    if gradient:
        corner_colors = get_colors_corners(fit_image)
    else:
        corner_colors = [NEUTRAL_BG_COLOR]*4

    final_image = draw_gradient_bg((width, height), corner_colors)
    final_image.paste(fit_image, (int(left), int(top)))
    return final_image

