# Airrohr2MQTT

Gateway between airrohr API and MQTT

This service will listen for Data supplied via the
[Airrohr API](https://github.com/opendata-stuttgart/meta/wiki/APIs)
and publish MQTT payloads compatible with
[Home Assistant auto discovery](https://www.home-assistant.io/docs/mqtt/discovery/).  

Gateway code based on https://github.com/joba-1/airrohr2domoticz