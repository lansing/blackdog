
import argparse
from typing import Optional
import structlog
import os
from smart_open import open

from mpd import MPDClient
from blackdog.sources import DEFAULT_DISPLAY_SERVER_URL
from blackdog.sources.abstract import Source

log_level = os.getenv("LOGLEVEL", "INFO").upper()
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)
log = structlog.get_logger()


class MPDConfig:
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 6600,
                 coverart_url: str = "http://localhost/coverart.php"):
        self.host = host
        self.port = port
        self.coverart_url = coverart_url

class MPD(Source):

    def __init__(self, display_url: str, mpd_config: MPDConfig):
        super().__init__(display_url)
        self.mpd_config = mpd_config
        self._client: Optional[MPDClient] = None

    def get_client(self):
        try:
            if not self._client:
                self._client = MPDClient()
            self._client.connect(self.mpd_config.host, self.mpd_config.port)
            log.debug(event="mpd_connect",
                      host=self.mpd_config.host,
                      port=self.mpd_config.port)
            return self._client
        except Exception as e:
            log.exception("error_mpd_connect",
                          host=self.mpd_config.host,
                          port=self.mpd_config.port)
            raise e

    def run(self):
        client = self.get_client()
        while True:
            events = client.idle()
            if 'player' in events:
                log.debug("mpd_player_event")
                song = client.currentsong()
                if 'file' in song:
                    filename = song['file']
                    url = f"{self.mpd_config.coverart_url}/{filename}"
                    log.debug("mpd_fetch_coverart", file=filename, url=url)
                    image = open(url, 'rb').read()
                    self.display(image)

def main():
    parser = argparse.ArgumentParser(description="BlackDog source for MPD (with coverart via Moode)")
    
    parser.add_argument(
        '--display_url', 
        type=str, 
        default=DEFAULT_DISPLAY_SERVER_URL, 
        help='URL for display server endpoint'
    )
    parser.add_argument(
        '--mpd_host', 
        type=str, 
        default="localhost", 
        help='MPD hostname'
    )
    parser.add_argument(
        '--mpd_port', 
        type=int, 
        default=6600, 
        help='MPD port'
    )
    parser.add_argument(
        '--coverart_url', 
        type=str, 
        default="http://localhost/coverart.php/", 
        help='Prefix for coverart fetch url (normally provided by Moode)'
    )
    
    args = parser.parse_args()
    mpd_config = MPDConfig(host=args.mpd_host, port=args.mpd_port,
                           coverart_url=args.coverart_url)
    source = MPD(args.display_url, mpd_config=mpd_config)
    source.run()
    
if __name__ == "__main__":
    main()
