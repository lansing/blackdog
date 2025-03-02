import argparse
from typing import Optional
import io
import glob
import random
import structlog
import os
from threading import Event, Thread

from smart_open import open
from PIL import Image

from blackdog.sources import DEFAULT_DISPLAY_SERVER_URL
from blackdog.sources.abstract import Source

log_level = os.getenv("LOGLEVEL", "INFO").upper()
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)
log = structlog.get_logger()


class ScreenSaverConfig:
    def __init__(self, art_dir: str):
        self.art_dir = art_dir


class ScreenSaverThread(Thread):
    def __init__(self, wait: int, callback):
        Thread.__init__(self)
        self.wait = wait
        self.callback = callback
        self.stopped = Event()

    def run(self):
        while not self.stopped.wait(self.wait):
            self.callback()

    def stop(self):
        self.stopped.set()


class ScreenSaver(Source):

    REFRESH_INTERVAL = 60    # update display interval
    ROTATE_INTERVAL = 60*60  # change the image

    def __init__(self, display_url: str, config: ScreenSaverConfig):
        super().__init__(display_url)
        self.config = config
        self.current_image: Optional[bytes] = None
        self.refresh_thread: Optional[ScreenSaverThread] = None
        self.image_queue = []

    def run(self):
        log.debug(event="screen_saver_run_start_thread_refresh", interval=self.REFRESH_INTERVAL)
        self.refresh_thread = ScreenSaverThread(self.REFRESH_INTERVAL, self._refresh)
        self.refresh_thread.start()
        log.debug(event="screen_saver_run_start_thread_rotate", interval=self.ROTATE_INTERVAL)
        self.rotate_thread = ScreenSaverThread(self.ROTATE_INTERVAL, self._rotate)
        self.rotate_thread.start()
        
    def _rotate(self):
        self.current_image = self._get_random_image()

    def _refill_image_queue(self):
        subdirs = glob.glob(f"{self.config.art_dir}/*")
        subdirs.sort()
        current = subdirs[-1]
        self.image_queue = glob.glob(f"{current}/*")

    def _get_random_image(self):
        if len(self.image_queue) == 0:
            self._refill_image_queue()
        i = random.randint(0, len(self.image_queue)-1)
        image_path = self.image_queue.pop(i)
        image_data = open(image_path, 'rb').read()
        return image_data

    def _refresh(self):
        if self.current_image:
            self.display(self.current_image, gradient=False, capture=False)
        

def main():
    parser = argparse.ArgumentParser(description="BlackDog ScreenSaver")

    parser.add_argument(
        '--display_url', 
        type=str, 
        default=DEFAULT_DISPLAY_SERVER_URL, 
        help='URL for display server endpoint'
    )
    parser.add_argument(
        '--art_dir', 
        type=str, 
        default="",  # TODO add a default dir 
        help='Directory containing screensaver art'
    )
    
    args = parser.parse_args()
    config = ScreenSaverConfig(art_dir=args.art_dir)
    source = ScreenSaver(args.display_url, config=config)
    source.run()
    
if __name__ == "__main__":
    main()

