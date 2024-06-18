#!/bin/bash
import threading
import os
import logging
import sys
import time
import argparse
import dotenv
import requests

from lib.dht22 import DHT22
from lib.cold import Cold
from lib.fixture import LightFixture
from lib.mqtt_client import MqttClient

if __name__ == "__main__":
    # --- Define the command line arguments ---
    parser = argparse.ArgumentParser(description="Your script's description")
    parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")

    args = parser.parse_args()

    # --- Define the logger ---
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # --- Define the environment variables ---
    dotenv.load_dotenv("/home/lab/Desktop/rasp-bottom/.env")
    os.environ["key"] = "valores"
    dotenv.set_key("/home/lab/Desktop/rasp-bottom/.env", "key", os.environ["key"])
    
    # Device Keys
    DHT22_SENSOR_KEY = os.environ.get("DHT22_SENSOR_KEY", "dht22_key")
    PUMP_ACTUATOR_KEY = os.environ.get("PUMP_ACTUATOR_KEY", "pump_key")
    LIGHT_FIXTURE_KEY = os.environ.get("LIGHT_FIXTURE_KEY", "light_fixture_key")
    
    # Device IDs
    DHT22_SENSOR_ID_2 = os.environ.get("DHT22_SENSOR_ID_2", "dht22:002")
    LIGHT_FIXTURE_ID_3 = os.environ.get("LIGHT_FIXTURE_ID_3", "light_fixture:003")
    LIGHT_FIXTURE_ID_4 = os.environ.get("LIGHT_FIXTURE_ID_4", "light_fixture:004")

    # --- Define mqtt client ---
    mqtt_client = MqttClient()

    # --- Define the devices ---
    # DHT22 sensor
    dht22_sensor_2 = DHT22(mqtt_client, DHT22_SENSOR_KEY, DHT22_SENSOR_ID_2)
    
    # Light fixture
    light_fixture_3 = LightFixture(mqtt_client, LIGHT_FIXTURE_KEY, LIGHT_FIXTURE_ID_3)
    light_fixture_4 = Cold(mqtt_client, LIGHT_FIXTURE_KEY, LIGHT_FIXTURE_ID_4)


    # --- Define and start the threads ---
    threads = []
    
    threads.append(
        threading.Thread(target=mqtt_client.connect, daemon=True)
    )

    threads.append(
        threading.Thread(target=dht22_sensor_2.run, daemon=True)
    )
    threads.append(
        threading.Thread(target=light_fixture_3.run, daemon=True)
    )
    
    threads.append(
        threading.Thread(target=light_fixture_4.run, daemon=True)
    )

    for thread in threads:
        thread.start()

    # --- Keep the main thread running ---
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Ctrl+C pressed")
        logging.info("Exiting...")
        sys.exit(0)