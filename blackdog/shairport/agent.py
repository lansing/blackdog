import base64
import io
import requests
import time

import paho.mqtt.client as mqtt

DISPLAY_HOST = "localhost"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "shairport"


SUBTOPICS = [
    "artist",
    "album",
    "title",
    "cover"
]

DEFAULT_MIME = "image/png"

def subtopic_full(subtopic):
    topic = MQTT_TOPIC + "/" + subtopic
    return topic

def image_mime(image):
    if image.startswith(b"\xff\xd8"):
        return "image/jpeg"
    elif image.startswith(b"\x89PNG\r\n\x1a\r"):
        return "image/png"
    else:
        return "image/jpg"

def on_connect(client, userdata, flags, rc):
     for subtopic in SUBTOPICS:
        full_topic = subtopic_full(subtopic)
        print(f"subscribe: {full_topic}")
        (result, msg_id) = client.subscribe(full_topic, 0)

def on_message(client, userdata, message):
    if message.topic != subtopic_full("cover"):
        print(message.topic, message.payload)

    if message.topic == subtopic_full("cover"):
        print("cover update")
        if message.payload:
            mime_type = image_mime(message.payload)
            image = message.payload
            print(f"Got {len(image)} byes")
            on_coverart(image)


last_image = None

def on_coverart(image):
    global last_image
    if last_image != image:
        last_image = image
        image_io = io.BytesIO(image)
        print("Posting to display server")
        try:
            requests.post(f"http://{DISPLAY_HOST}:8888/imagez",
                        files = {"image": image_io})
        except Exception as e:
            print(f"Error: {str(e)}")
    else:
        print("No change")


# Configure MQTT broker connection
mqttc = mqtt.Client()

# register callbacks
mqttc.on_connect = on_connect
mqttc.on_message = on_message

while True:
    try:
        print("Connecting to broker", MQTT_HOST, "port", MQTT_PORT)
        mqttc.connect(MQTT_HOST, port=MQTT_PORT)

        # loop_start run a thread in the background
        mqttc.loop_forever()

    except ConnectionRefusedError as e:
        print(e)
        time.sleep(5)

