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

while True:
    try:
        events = client.idle()
        if 'player' in events:
            song = client.currentsong()
            if 'file' in song:
                filename = song['file']
                if filename is not last_filename:
                    url = f"http://{MOODE_HOST}/coverart.php/{filename}"
                    print(url)
                    image = open(url, 'rb').read()
                    print(f"fetched {len(image)} bytes")
    except ConnectionError as e:
        client = get_client
    # TODO catch smart_open errors

