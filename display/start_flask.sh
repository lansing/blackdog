#!/bin/bash

source /home/pi/.virtualenvs/album-art-agent/bin/activate

export FLASK_APP=display-server.py
export FLASK_ENV=development

cd /home/pi/Code/album-art-agent/display/

flask run --port 8888 --host=0.0.0.0
