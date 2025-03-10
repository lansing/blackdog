import argparse
from datetime import datetime
from typing import Optional
import glob
import random
import structlog
import os
from threading import Event, Thread

from smart_open import open
import numpy as np

from blackdog.sources import DEFAULT_DISPLAY_SERVER_URL
from blackdog.sources.abstract import Source

log_level = os.getenv("LOGLEVEL", "INFO").upper()
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)
log = structlog.get_logger()


REFRESH_INTERVAL = 60    # update display interval
ROTATE_INTERVAL = 60*60  # change the image


class ScreenSaverConfig:
    def __init__(self,
                 art_dir: str,
                 capture: int=0,
                 rotate: int = ROTATE_INTERVAL,
                 daily_dir: bool = False):
        self.art_dir = art_dir
        self.capture = capture
        self.rotate = rotate
        self.daily_dir = daily_dir


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

    def __init__(self, display_url: str, config: ScreenSaverConfig):
        super().__init__(display_url)
        self.config = config
        self.current_image: Optional[bytes] = None
        self.refresh_thread: Optional[ScreenSaverThread] = None
        self.image_queue = []

    def run(self):
        self._rotate()
        log.debug(event="screen_saver_run_start_thread_rotate", interval=self.config.rotate)
        self.rotate_thread = ScreenSaverThread(self.config.rotate, self._rotate)
        self.rotate_thread.start()
        self._refresh()
        log.debug(event="screen_saver_run_start_thread_refresh", interval=REFRESH_INTERVAL)
        self.refresh_thread = ScreenSaverThread(REFRESH_INTERVAL, self._refresh)
        self.refresh_thread.start()
        
    def _rotate(self):
        log.debug(event="screen_saver_rotate", interval=self.config.rotate)
        self.current_image = self._get_random_image()

    def _refill_image_queue(self):
        if not self.config.art_dir:
            raise Exception("You must provide an art_dir in the config")
        log.debug(event="refill_begin", art_dir=self.config.art_dir)
        contents = glob.glob(f"{self.config.art_dir}/*")
        subdirs = list(filter(lambda path: os.path.isdir(path), contents))
        if subdirs:
            # only use the last subdir
            subdirs.sort()
            if self.config.daily_dir:
                yday = datetime.today().timetuple().tm_yday
                todays_idx = np.random.RandomState(yday).randint(len(subdirs))
                current = subdirs[todays_idx]
                log.debug(event="refill_subdir_daily", yday=yday, todays_idx=todays_idx)
            else:
                current = subdirs[-1]
            self.image_queue = glob.glob(f"{current}/*")
            log.debug(event="refill_subdir", art_dir=current, num_images=len(self.image_queue))
        else:
            files = list(filter(lambda path: not os.path.isdir(path), contents))
            self.image_queue = files
            log.debug(event="refill_parent", art_dir=self.config.art_dir,
                      num_images=len(self.image_queue))

    def _get_random_image(self):
        if len(self.image_queue) == 0:
            self._refill_image_queue()
        i = random.randint(0, len(self.image_queue)-1)
        image_path = self.image_queue.pop(i)
        with open(image_path, 'rb') as file:
            return file.read()

    def _refresh(self):
        log.debug(event="screen_saver_refresh")
        if self.current_image:
            self.display(self.current_image, gradient=False, capture=self.config.capture)
        

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
        required=True,
        # default="",  # TODO add a default dir 
        help='Directory containing screensaver art'
    )
    parser.add_argument(
        '--capture', 
        type=int, 
        default=0, 
        help='Interval in seconds with which to capture display (for testing perhaps)'
    )
    parser.add_argument(
        '--rotate', 
        type=int, 
        default=ROTATE_INTERVAL, 
        help='Image rotation interval in seconds'
    )
    parser.add_argument(
        '--daily_dir', 
        action='store_true',
        help='Rotate to a new subdirectory of art_dir each day'
    )

    args = parser.parse_args()
    config = ScreenSaverConfig(art_dir=args.art_dir, capture=args.capture, rotate=args.rotate)
    source = ScreenSaver(args.display_url, config=config)
    source.run()
    
if __name__ == "__main__":
    main()

