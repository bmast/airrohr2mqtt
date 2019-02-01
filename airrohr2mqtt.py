#!/usr/bin/env python3

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

import paho.mqtt.client as mqtt


class Gateway(BaseHTTPRequestHandler):
    """
    process sensor data supplied via airrohr API
    and publish Home Assistant compatible MQTT payloads
    """
    mqtt_server = None

    def __respond(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "text/ascii")
        self.send_header("Content-Length", len(bytes(message, "utf8")))
        self.end_headers()
        self.wfile.write(bytes(message, "utf8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        sensor_data = json.loads(self.rfile.read(content_length).decode("utf-8"))
        mqtt_data = dict()
        attributes = dict()
        for (key, value) in sensor_data.items():
            if key != "sensordatavalues":
                attributes[key] = value
        sensor_name = "luftdaten_%s" % attributes["esp8266id"]
        attributes_topic = "home/Sensor/%s/attributes" % sensor_name
        state_topic = "home/sensor/%s/state" % sensor_name

        # publish discovery information
        for sensor in sensor_data["sensordatavalues"]:
            value_type = sensor["value_type"]
            mqtt_data[value_type] = sensor["value"]
            cfg_topic = "homeassistant/sensor/%s_%s/config" % (sensor_name, value_type)
            config_data = {
                "name": "%s_%s" % (sensor_name, value_type),
                "json_attributes_topic": attributes_topic,
                "state_topic": state_topic,
                "value_template": "{{value_json.%s}}" % value_type
            }
            if "humidity" in value_type:
                config_data["unit_of_meas"] = "%"
                config_data["icon"] = "mdi:water-percent"
            elif "temperature" in value_type:
                config_data["unit_of_meas"] = "°C"
                config_data["icon"] = "mdi:thermometer"
            elif "SDS_P" in value_type:
                config_data["unit_of_meas"] = "µg/m3"
                if value_type.endswith("P1"):
                    # PM10
                    config_data["icon"] = "mdi:thought-bubble"
                elif value_type.endswith("P2"):
                    # PM2.5
                    config_data["icon"] = "mdi:thought-bubble-outline"
            elif value_type == "BME280_pressure":
                config_data["unit_of_meas"] = "Pa"
                config_data["icon"] = "mdi:arrow-down-bold"
            self.__publish_mqtt(cfg_topic, json.dumps(config_data))

        # publish sensor data
        self.__publish_mqtt(state_topic, json.dumps(mqtt_data))
        self.__publish_mqtt(attributes_topic, json.dumps(attributes))
        self.__respond(200, "OK")

    def __publish_mqtt(self, topic, data):
        client = mqtt.Client()
        client.connect(self.mqtt_server)
        client.publish(topic, data)
        client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Airrohr2MQTT gateway")
    parser.add_argument("--port", type=int, default=8042)
    parser.add_argument("--mqtt-server", type=str, default="localhost")
    args = parser.parse_args()
    Gateway.mqtt_server = args.mqtt_server
    httpd = HTTPServer(("", args.port), Gateway)
    try:
        print("starting Airrohr2MQTT gateway on port %d" % args.port)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("interrupted")
    httpd.server_close()
    print("Airrohr2MQTT gateway stopped")
