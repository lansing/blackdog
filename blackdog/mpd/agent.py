import requests
import io
import time

from mpd import MPDClient
from mpd.base import ConnectionError
from smart_open import open

MOODE_HOST = "localhost"
DISPLAY_HOST = "localhost"

def get_client():
    client = MPDClient()
    client.connect(MOODE_HOST, 6600)
    print(f"Connected to {MOODE_HOST} running mpd {client.mpd_version}")
    return client

client = None

last_filename = None
last_image = None

def on_coverart(image):
    global last_image
    global last_filename
    if image != last_image:
        print(f"fetched {len(image)} bytes")
        last_filename = filename
        last_image = image
        image_io = io.BytesIO(image)
        print("Posting to display server")
        requests.post(f"http://{MOODE_HOST}:8888/imagez",
                      files = {"image": image_io})
    else:
        print("No change")


while True:
    try:
        if not client:
          client = get_client()
        events = client.idle()
        if 'player' in events:
            song = client.currentsong()
            if 'file' in song:
                filename = song['file']
                if filename != last_filename:
                    url = f"http://{DISPLAY_HOST}/coverart.php/{filename}"
                    print(url)
                    image = open(url, 'rb').read()
                    on_coverart(image)

    except (ConnectionError, ConnectionResetError, ConnectionRefusedError) as e:
        print(e)
        time.sleep(5)
        client = get_client()

