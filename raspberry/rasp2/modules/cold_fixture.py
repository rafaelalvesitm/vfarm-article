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
import datetime


class Cold():
    def __init__(self, mqtt_client, sensor_key, sensor_id):
        # --- Set environement file --- 
        self.dotenv_file = "/home/lab/Desktop/rasp-bottom/.env"
        
        # --- Sensor Attributes as defined in the IoT Agent JSON ---
        self.sensor_key = sensor_key  # API Key from IoT Agent JSON
        self.sensor_id = sensor_id  # API Key from IoT Agent JSON

        # Sensor Attributes as defined in the IoT Agent JSON
        self.startTime = os.environ.get(f"{self.sensor_id}_startTime", "10:00:00")
        self.endTime = os.environ.get(f"{self.sensor_id}_endTime", "20:00:00")
        self.status = os.environ.get(f"{self.sensor_id}_status", "off") 
        self.collectInterval = int(os.environ.get(f"{self.sensor_id}_collectInterval", "60"))

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
            "status": self.status,
        }

    # --- MQTT Callbacks ---
    def receive_commands(self, client, userdata, message):
        payload = json.loads(message.payload.decode())

        if payload.get("setStartTime"):
            self.update_start_time(payload.get("setStartTime"))
        elif payload.get("setEndTime"):
            self.update_end_time(payload.get("setEndTime"))
        elif self.get("setCollectInterval"):
            self.update_collect_interval(payload.get("setCollectInterval"))

    def update_start_time(self, startTime):
        logging.debug(
            f"Device: {self.sensor_id} | Start Time updated to {self.startTime}"
        )
        self.startTime = startTime
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_startTime", str(self.startTime))

        data = {
            "st": self.startTime,
            "setStartTime_info": f"Updated to {self.startTime,}",
            "setStartTime_status": "OK",
        }
        payload = json.dumps(data)
        self.mqtt_client.publish(self.attrs_topic, payload)

    def update_end_time(self, endTime):
        logging.debug(
            f"Device: {self.sensor_id} | End Time updated to {self.endTime}"
        )
        self.endTime = endTime
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_startTime", str(self.endTime))

        data = {
            "et": self.endTime,
            "setEndTime_info": f"Updated to {self.endTime,}",
            "setEndTime_status": "OK",
        }
        payload = json.dumps(data)
        self.mqtt_client.publish(self.attrs_topic, payload)
        
    def update_collect_interval(self, collectInterval):
        logging.debug(
            f"Device: {self.sensor_id} | Collect Interval updated to {self.collectInterval}"
        )
        self.collectInterval = collectInterval
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_collectInterval", str(self.collectInterval))

        data = {
            "collectInterval": self.collectInterval,
            "setCollectInterval_info": f"Updated to {self.collectInterval,}",
            "setCollectInterval_status": "OK",
        }
        payload = json.dumps(data)
        self.mqtt_client.publish(self.attrs_topic, payload)

    # --- Utility methods
    def is_between(self):
        start_time = datetime.datetime.strptime(self.startTime, "%H:%M:%S").time()
        end_time = datetime.datetime.strptime(self.endTime, "%H:%M:%S").time()
        now = datetime.datetime.now().time()
        if start_time < end_time:
            return start_time <= now <= end_time
        else:
            return start_time <= now or now <= end_time

    # --- Main device methods
    def actuate(self):
        logging.debug(f"Actuating {self.sensor_id}")
        if self.is_between():
            # Turn the pump on
            self.status = "On"
            GPIO.output(self.pin, GPIO.HIGH)
        elif not self.is_between():
            # Turn the pump off
            self.status = "Off"
            GPIO.output(self.pin, GPIO.LOW)

    def save_data(self):
        logging.debug(f"Saving data to sqlite {self.sensor_id}")
        # Create table
        try:
            conn = sqlite3.connect("/home/lab/Desktop/rasp-bottom/data-bottom.db")
            cur = conn.cursor()
            table_name = f"`{self.sensor_id}`"
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"
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
                "st": self.startTime,
                "et": self.endTime,
                "timestamp": time.time()
            }
            payload = json.dumps(message)
            self.mqtt_client.publish(self.attrs_topic, payload)
        except Exception as e:
            logging.error(f"Device: {self.sensor_id} | Send to MQTT | Error: {e}")

    # --- Main Loop ---
    def run(self):
        while True:
            logging.info(f"Cold LED object: {self.__dir__()}")
            self.actuate()
            self.save_data()
            self.send_data()
            time.sleep(self.collectInterval)