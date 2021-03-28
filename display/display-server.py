import io

from flask import Flask
from flask import request
from PIL import Image
from inky.inky_uc8159 import Inky
from colorthief import ColorThief


inky = Inky()
saturation = 0.7

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Display Server'

@app.route('/imagez', methods=['POST'])
def image():
    f = request.files['image']
    image_data = f.read()
    image = Image.open(io.BytesIO(image_data))

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

    fit_image_bytes = io.BytesIO()
    fit_image.save(fit_image_bytes, format='PNG')
    color_thief = ColorThief(fit_image_bytes)
    dominant_color = color_thief.get_color(quality=1)
    
    left = (600 - fit_image.size[0]) // 2

    final_image = Image.new(image.mode, (600, 448), dominant_color)
    final_image.paste(fit_image, (int(left), 0))

    #return(f"{final_image.size[0]} {final_image.size[1]}")


    inky.set_image(final_image, saturation=saturation)
    inky.show()

    return "Done"

    


