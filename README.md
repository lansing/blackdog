# Black Dog - E Ink Album Art Display

## Overview 

Black Dog turns your Raspberry Pi audio source, plus Inky Expression 7-color E Ink display, into a beautiful
album art display for your hifi system.

Black Dog has been developed against the Moode Audio system as a target, but it should work with any
Raspberry Pi being used as an audio source. It currently supports two renderers: Shairport Sync, for AirPlay
support, and Music Player Daemon. 

Agents have been implemented for each renderer. The agents list for album art update
change events, and post the new album art image to a shared display server. 

It should be possible to add support for any other audio renderer that
provides album art metadata in some way, or implement agents that consume other image data sources.

One such alternative agent has been implemented, a screen saver module. When music isn't playing,
the screen saver rotates through a curated selection of images.


## Hardware Requirements

- Raspberry Pi of some sort (I'm using a 4), plus normal accessories (power adapter, SD card, etc)
- Inky Expression 7-color E Ink display
- DAC compatible with Moode audio: USB, I2C, HDMI out... many possibilities
- BYO stereo, of course


## Install

- Install Moode Audio on your boot disk and configure to your liking

- Run the setup script:

```
sudo curl -L https://raw.githubusercontent.com/lansing/blackdog/refs/heads/master/setup.sh | bash
```

- Make sure your Inky Expression is plugged in to your GPIO pins

- Play some tunes and enjoy the album art
