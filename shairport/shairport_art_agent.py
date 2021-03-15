import base64

import paho.mqtt.client as mqtt

MQTT_HOST = "hifi.local"
MQTT_PORT = 1883
MQTT_TOPIC = "shairport-sync/hifi"


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
        (result, msg_id) = client.subscribe(subtopic_full(subtopic), 0)

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
        # push to display
    else:
        print("No change")


# Configure MQTT broker connection
mqttc = mqtt.Client()

# register callbacks
mqttc.on_connect = on_connect
mqttc.on_message = on_message

print("Connecting to broker", MQTT_HOST, "port", MQTT_PORT)
mqttc.connect(MQTT_HOST, port=MQTT_PORT)

# loop_start run a thread in the background
mqttc.loop_start()

input()
