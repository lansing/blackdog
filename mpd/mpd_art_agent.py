from mpd import MPDClient
from mpd.base import ConnectionError
from smart_open import open

MOODE_HOST = "hifi.local"

def get_client():
    client = MPDClient()
    client.connect(MOODE_HOST, 6600)
    print(f"Connected to {MOODE_HOST} running mpd {client.mpd_version}")
    return client

client = get_client()

last_filename = None
last_image = None

def on_coverart(image):
    global last_image
    global last_filename
    if image != last_image:
        print(f"fetched {len(image)} bytes")
        last_filename = filename
        last_image = image
        # push to display
    else:
        print("No change")


while True:
    try:
        events = client.idle()
        if 'player' in events:
            song = client.currentsong()
            if 'file' in song:
                filename = song['file']
                if filename != last_filename:
                    url = f"http://{MOODE_HOST}/coverart.php/{filename}"
                    print(url)
                    image = open(url, 'rb').read()
                    on_coverart(image)

    except ConnectionError as e:
        client = get_client
    # TODO catch smart_open errors

