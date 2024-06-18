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
import RPi.GPIO as GPIO

# from lib.mqtt_client import MqttClient


class Pump():
    def __init__(self, mqtt_client, sensor_key, sensor_id):
        
        # --- Set environement file --- 
        self.dotenv_file = "/home/lab/Desktop/rasp-top/.env"
        
        # --- Sensor Attributes as defined in the IoT Agent JSON ---
        self.sensor_key = sensor_key  # API Key from IoT Agent JSON
        self.sensor_id = sensor_id  # API Key from IoT Agent JSON

        # Sensor Attributes as defined in the IoT Agent JSON
        self.onInterval = int(os.environ.get(f"{self.sensor_id}_onInterval", "5"))
        self.offInterval = int(os.environ.get(f"{self.sensor_id}_offInterval", "10"))
        self.status = os.environ.get(f"{self.sensor_id}_status", "off") 

        # MQTT Topics as defined in the IoT Agent JSON
        self.attrs_topic = f"/json/{self.sensor_key}/{self.sensor_id}/attrs"
        self.cmd_topic = f"/{self.sensor_key}/{self.sensor_id}/cmd"
        
        # --- Device attributes need for the GPIO library ---
        self.pin = int(os.environ.get(f"{self.sensor_id}_PIN", "17"))
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)

        # --- MQTT Client Inheritence ---
        # super().__init__()
        self.mqtt_client = mqtt_client
        self.mqtt_client.connect()
        self.mqtt_client.subscribe(self.cmd_topic)
        self.mqtt_client.message_callback_add(self.cmd_topic, self.receive_commands)

    # --- Magic Methods ---
    def __dir__(self):
        return {
            "sensor_key": self.sensor_key,
            "sensor_id": self.sensor_id,
            "onInterval": self.onInterval,
            "offInterval": self.offInterval,
            "status": self.status,
        }

    def receive_commands(self, client, userdata, message):
        payload = json.loads(message.payload.decode())
        logging.info("Received command: %s", payload)

        if payload.get("setOnInterval"):
            self.update_on_interval(payload.get("setOnInterval"))
        elif payload.get("setOffInterval"):
            self.update_off_interval(payload.get("setOffInterval"))

    def update_on_interval(self, onInterval):
        self.onInterval = onInterval
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_onInterval", str(self.onInterval))

        logging.info("Device: {self.sensor_id} | On interval updated to {self.onInterval}")
        data = {
            "on": self.onInterval,
            "setOnInterval_info": f"Updated to {self.onInterval} seconds",
            "setOnInterval_status": "OK",
        }
        payload = json.dumps(data)
        self.mqtt_client.publish(self.attrs_topic, payload)

    def update_off_interval(self, offInterval):
        logging.debug(
            f"Device: {self.sensor_id} | On interval updated to {self.offInterval}"
        )
        self.offInterval = offInterval
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_offInterval", str(self.offInterval))

        data = {
            "off": self.offInterval,
            "setOffInterval_info": f"Updated to {self.offInterval} seconds",
            "setOffInterval_status": "OK",
        }
        payload = json.dumps(data)
        self.mqtt_client.publish(self.attrs_topic, payload)

    # --- Main device methods
    def actuate(self):
        logging.debug(f"Actuating {self.sensor_id}")
        if self.status == "on":
            # Turn the pump on
            GPIO.output(self.pin, GPIO.HIGH)
        elif self.status == "off":
            # Turn the pump off
            GPIO.output(self.pin, GPIO.LOW)

    def save_data(self):
        logging.debug(f"Saving data to sqlite {self.sensor_id}")
        # Create table
        try:
            conn = sqlite3.connect("/home/lab/Desktop/rasp-top/data-top.db")
            cur = conn.cursor()
            table_name = f"`{self.sensor_id}`"
            cur.execute(
                f"""CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT
                )"""
            )
            cur.execute(
                f"INSERT INTO {table_name} (status) VALUES (?)", (self.status,)
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Device: {self.sensor_id} | Save to SQL | Error: {e}")

    def send_data(self):
        logging.debug(f"Sending data to MQTT {self.sensor_id}")
        try:
            message = {
                "s": self.status, 
                "on": self.onInterval,
                "off": self.offInterval,
                "timestamp": time.time()
            }
            payload = json.dumps(message)
            self.mqtt_client.publish(self.attrs_topic, payload)
        except Exception as e:
            logging.error(f"Device: {self.sensor_id} | Send to MQTT | Error: {e}")

    # --- Main Loop ---
    def run(self):
        while True:
            logging.info(f"Pump object: {self.__dir__()}")
            self.actuate()
            self.save_data()
            self.send_data()
            if self.status == "on":
                time.sleep(self.onInterval)
                self.status = "off"
            elif self.status == "off":
                time.sleep(self.offInterval)
                self.status = "on"