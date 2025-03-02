import argparse
from paho.mqtt.enums import CallbackAPIVersion
import structlog
import os

from paho.mqtt.client import Client, MQTTMessage
from blackdog.sources import DEFAULT_DISPLAY_SERVER_URL
from blackdog.sources.abstract import Source


log_level = os.getenv("LOGLEVEL", "INFO").upper()
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(log_level),
)
log = structlog.get_logger()

class MQTTConfig:
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 1883,
                 topic: str = 'shairport'):
        self.host = host
        self.port = port
        self.topic = topic


class Shairport(Source):

    SUBTOPICS = [
        "artist",
        "album",
        "title",
        "cover"
    ]

    def __init__(self, display_url, mqtt_config: MQTTConfig):
        super().__init__(display_url)
        self.mqtt_config = mqtt_config

    def run(self):
        mqttc = Client(callback_api_version=CallbackAPIVersion.VERSION2)
        mqttc.on_connect = self._mqtt_on_connect
        mqttc.on_message = self._mqtt_on_message

        try:
            log.debug(event="shairport_mqtt_attempt_connect",
                      host=self.mqtt_config.host,
                      port=self.mqtt_config.port)
            mqttc.connect(self.mqtt_config.host, port=self.mqtt_config.port)
            log.debug(event="shairport_mqtt_connected")
            mqttc.loop_forever()
        except ConnectionRefusedError as e:
            log.exception(event="shairport_mqtt_connect_failed",
                          message="could not connect to mqtt, is it running? check your config")
            raise e

    def _subtopic_full(self, subtopic: str):
        topic = "/".join([self.mqtt_config.topic, subtopic])
        return topic

    def _mqtt_on_connect(self, client, userdata, flags, rc, properties):
        for subtopic in self.SUBTOPICS:
            full_topic = self._subtopic_full(subtopic)
            (result, msg_id) = client.subscribe(full_topic, 0)
            log.debug(event="shairport_mqtt_subscribe",
                      topic=full_topic)

    def _mqtt_on_message(self, client: Client, userdata, message: MQTTMessage):
        if message.topic == self._subtopic_full("cover"):
            if message.payload:
                log.debug(event="shairport_mqtt_cover_message",
                          len=len(message.payload))
                self.display(message.payload)


def main():
    parser = argparse.ArgumentParser(description="BlackDog source for Shairport")
    
    parser.add_argument(
        '--display_url', 
        type=str, 
        default=DEFAULT_DISPLAY_SERVER_URL,
        help='URL for display server endpoint'
    )
    parser.add_argument(
        '--mqtt_host', 
        type=str, 
        default="localhost", 
        help='MQTT hostname'
    )
    parser.add_argument(
        '--mqtt_port', 
        type=int, 
        default=1883, 
        help='MQTT port'
    )
    parser.add_argument(
        '--mqtt_topic', 
        type=str, 
        default="shairport", 
        help='MQTT topic'
    )
    
    args = parser.parse_args()
    mqtt_config = MQTTConfig(host=args.mqtt_host, port=args.mqtt_port,
                             topic=args.mqtt_topic)
    source = Shairport(args.display_url, mqtt_config=mqtt_config)
    source.run()
    
if __name__ == "__main__":
    main()
