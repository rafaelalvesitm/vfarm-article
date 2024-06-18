import threading
import os
import logging
import sys
import time
import argparse
import dotenv
import requests

from lib.dht22 import DHT22
from lib.pump import Pump
from lib.fixture import LightFixture
from lib.mqtt_client import MqttClient

if __name__ == "__main__":
    # --- Define the command line arguments ---
    parser = argparse.ArgumentParser(description="Run devices connected to the `Raspberry Pi top` gateway")
    parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")

    args = parser.parse_args()

    # --- Define the logger ---
    log_level = logging.DEBUG if args.debug else logging.INFO # Set the log level to DEBUG if the debug flag is set
    logging.basicConfig(
        level=log_level, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # --- Define the environment variables ---
    dotenv.load_dotenv("/home/lab/Desktop/rasp-top/.env")

    # Device Keys
    DHT22_SENSOR_KEY = os.environ.get("DHT22_SENSOR_KEY")
    PUMP_ACTUATOR_KEY = os.environ.get("PUMP_ACTUATOR_KEY")
    LIGHT_FIXTURE_KEY = os.environ.get("LIGHT_FIXTURE_KEY")

    # Device IDs
    DHT22_SENSOR_ID_1 = os.environ.get("DHT22_SENSOR_ID_1")
    PUMP_ACTUATOR_ID_1 = os.environ.get("PUMP_ACTUATOR_ID_1")
    LIGHT_FIXTURE_ID_1 = os.environ.get("LIGHT_FIXTURE_ID_1")
    LIGHT_FIXTURE_ID_2 = os.environ.get("LIGHT_FIXTURE_ID_2")
    
    # --- Define the mqtt client ---
    
    mqtt_client = MqttClient( )

    # --- Define the devices ---
    # DHT22 sensor
    dht22_sensor_1 = DHT22(mqtt_client, DHT22_SENSOR_KEY, DHT22_SENSOR_ID_1)

    # Pump actuator
    pump_actuator_1 = Pump(mqtt_client, PUMP_ACTUATOR_KEY, PUMP_ACTUATOR_ID_1)

    # Light fixture
    light_fixture_1 = LightFixture(mqtt_client, LIGHT_FIXTURE_KEY, LIGHT_FIXTURE_ID_1)
    light_fixture_2 = LightFixture(mqtt_client, LIGHT_FIXTURE_KEY, LIGHT_FIXTURE_ID_2)


    # --- Define and start the threads ---
    threads = []

    threads.append(
        threading.Thread(target=dht22_sensor_1.run, daemon=True)
    )
    threads.append(
        threading.Thread(target=pump_actuator_1.run, daemon=True)
    )
    threads.append(
        threading.Thread(target=light_fixture_1.run, daemon=True)
    )

    threads.append(
        threading.Thread(target=light_fixture_2.run, daemon=True)
    )


    # Start all threads
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