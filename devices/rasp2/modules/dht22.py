"""
Author: Rafael Gomes Alves
Description: This script uses an object oriented programming to simulate a DHT22 sensor. 
The sensor class should be able to:
- Read a config file with the following information:
    - MQTT broker address
    - MQTT broker port
    - MQTT client id
    - Sensor API key
    - Sensor ID
- Read the temperature and humidity data from the sensor
- Save this data to a SQLite database with the following schema:
    - id: integer, primary key, autoincrement
    - temperature: real
    - humidity: real
    - collectInterval: integer
    - timestamp: datetime, default current_timestamp
- Send this data to a MQTT broker in the topic /json/<api_key>/<device_id>/attrs with a JSON format
- Receive commands from the MQTT broker in the topic /<api_key>/<device_id>/cmd
"""

import random
import json
import time
import sqlite3
import logging
import os
import dotenv
import Adafruit_DHT
import RPi.GPIO as GPIO

# from lib.mqtt_client import MqttClient

class DHT22():
    def __init__(self, mqtt_client, sensor_key, sensor_id):
        # --- Set environement file --- 
        self.dotenv_file = "/home/lab/Desktop/rasp-bottom/.env"
        
        # --- Sensor Attributes as defined in the IoT Agent JSON ---
        self.sensor_key = sensor_key # API Key from IoT Agent JSON
        self.sensor_id = sensor_id # API Key from IoT Agent JSON
        
        # Sensor Attributes as defined in the IoT Agent JSON
        self.collectInterval = int(os.environ.get(f"{self.sensor_id}_collectInterval", "5"))
        self.temperature = None  # Temperature data
        self.humidity = None  # Humidity data

        # MQTT Topics as defined in the IoT Agent JSON
        self.attrs_topic = f"/json/{self.sensor_key}/{self.sensor_id}/attrs"
        self.cmd_topic = f"/{self.sensor_key}/{self.sensor_id}/cmd"
        
        # Sensor attributes need for the Adafruit_DHT library
        self.sensor = Adafruit_DHT.DHT22
        self.pin = int(os.environ.get(f"{self.sensor_id}_PIN", "4"))
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

        # --- MQTT Client Inheritence ---
        # super().__init__()
        self.mqtt_client = mqtt_client
        self.mqtt_client.connect()  
        self.mqtt_client.subscribe(self.cmd_topic)
        self.mqtt_client.message_callback_add(self.cmd_topic, self.receive_commands) 
        
    def __dir__(self):
        return {
            "sensor_key": self.sensor_key,
            "sensor_id": self.sensor_id,
            "collectInterval": self.collectInterval,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "attrs_topic": self.attrs_topic,
            "cmd_topic": self.cmd_topic,
        }

    # --- MQTT Callbacks ---
    def receive_commands(self, client, userdata, message):
        payload = json.loads(message.payload.decode())

        if payload.get("setCollectInterval"):
            self.update_collect_interval(payload["setCollectInterval"])

    def update_collect_interval(self, collectInterval):
        self.collectInterval = collectInterval
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_collectInterval", str(self.collectInterval))
        # Send the response to the MQTT Broker
        data = {
            "ci": self.collectInterval,
            "setCollectInterval_info": f"Updated to {self.collectInterval} seconds",
            "setCollectInterval_status": "OK",
        }
        payload = json.dumps(data)
        self.mqtt_client.publish(self.attrs_topic, payload)

    # --- Main sensor Methods ---
    def read_data(self):
        logging.debug(f"Reading data from {self.sensor_id}")
        try:
            self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        except Exception as e:
            logging.error(f"Device: {self.sensor_id} | Read data | Error: {e}")

    def save_data(self):
        logging.debug(f"Saving data to sqlite {self.sensor_id}")
        # Create table
        try:
            conn = sqlite3.connect("/home/lab/Desktop/rasp-bottom/data-bottom.db")
            cur = conn.cursor()
            table_name = f"`{self.sensor_id}`"
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, temperature REAL, humidity REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"
            )
            cur.execute(
                f"INSERT INTO {table_name} (temperature, humidity) VALUES (?, ?)",
                (self.temperature, self.humidity),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Device: {self.sensor_id} | Save to SQL | Error: {e}")

    def send_data(self):
        logging.debug(f"Sending data to MQTT {self.sensor_id}")
        try:
            if self.humidity is not None and self.temperature is not None:
                message = {
                    "t": self.temperature,
                    "rh": self.humidity,
                    "ci": self.collectInterval,
                    "timestamp": time.time()
                }
                payload = json.dumps(message)
                topic = f"/json/{self.sensor_key}/{self.sensor_id}/attrs"
                self.mqtt_client.publish(topic, payload)
        except Exception as e:
            logging.error(f"Device: {self.sensor_id} | Send to MQTT | Error: {e}")

    # --- Main Loop ---
    def run(self):
        while True:
            self.read_data()
            self.save_data()
            self.send_data()
            logging.info(f"DHT22 object: {self.__dir__()}")
            time.sleep(self.collectInterval)