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
import datetime
import dotenv

from lib.mqtt_client import MqttClient

from rpi_ws281x import Adafruit_NeoPixel, Color, ws


class LightFixture():
    def __init__(self, mqtt_client, sensor_key, sensor_id):
        # --- Set environement file --- 
        self.dotenv_file = "/home/lab/Desktop/rasp-top/.env"
        
        # --- Sensor Attributes ---
        self.sensor_key = sensor_key  # API Key from IoT Agent JSON
        self.sensor_id = sensor_id  # API Key from IoT Agent JSON

        # Sensor Attributes as defined in the IoT Agent JSON
        self.startTime = os.environ.get(f"{self.sensor_id}_startTime", "08:00:00")
        self.endTime = os.environ.get(f"{self.sensor_id}_endTime", "18:00:00")
        self.setRightRed = int(os.environ.get(f"{self.sensor_id}_setRightRed", "255"))
        self.setRightGreen = int(os.environ.get(f"{self.sensor_id}_setRightGreen", "255"))
        self.setRightBlue = int(os.environ.get(f"{self.sensor_id}_setRightBlue", "255"))
        self.setLeftRed = int(os.environ.get(f"{self.sensor_id}_setLeftRed", "255"))
        self.setLeftGreen = int(os.environ.get(f"{self.sensor_id}_setLeftGreen", "255"))
        self.setLeftBlue = int(os.environ.get(f"{self.sensor_id}_setLeftBlue", "255"))
        self.currentRightRed = 0
        self.currentRightGreen = 0
        self.currentRightBlue = 0
        self.currentLeftRed = 0
        self.currentLeftGreen = 0
        self.currentLeftBlue = 0
        self.collectInterval = int(os.environ.get(f"{self.sensor_id}_collectInterval", "60"))
        
        # Sensor attributes need for the rpi_ws281x library
        
        self.pixelCount = int(os.environ.get(f"{self.sensor_id}_LED_COUNT", "54"))
        self.pin = int(os.environ.get(f"{self.sensor_id}_LED_PIN", "18"))
        self.frequency = int(os.environ.get(f"{self.sensor_id}_LED_FREQ_HZ", "800000"))
        self.dma = int(os.environ.get(f"{self.sensor_id}_LED_DMA", "10"))
        self.invert = False
        self.brightness = int(os.environ.get(f"{self.sensor_id}_LED_BRIGHTNESS", "255"))
        self.channel = int(os.environ.get(f"{self.sensor_id}_LED_CHANNEL", "0"))
        self.strip_type = ws.WS2811_STRIP_GRB
        
        self.strip = Adafruit_NeoPixel(
            self.pixelCount,
            self.pin,
            self.frequency,
            self.dma,
            self.invert,
            self.brightness,
            self.channel,
            self.strip_type,
        )
        self.strip.begin()
        
        self.right_start = 0
        self.right_end = 27
        self.left_start = 27
        self.left_end = 55
    
        # MQTT Topics as defined in the IoT Agent JSON
        self.attrs_topic = f"/json/{self.sensor_key}/{self.sensor_id}/attrs"
        self.cmd_topic = f"/{self.sensor_key}/{self.sensor_id}/cmd"

        # --- MQTT Client Inheritence ---
        # super().__init__()
        self.mqtt_client = mqtt_client
        self.mqtt_client.connect()
        self.mqtt_client.subscribe(self.cmd_topic)
        self.mqtt_client.message_callback_add(self.cmd_topic, self.receive_commands)

    # --- Magic Methods ---
    def __dir__(self):
        return {
            "sensor_id": self.sensor_id,
            "timestamp": time.time(),
            "startTime": self.startTime,
            "endTime": self.endTime,
            "collectInterval": self.collectInterval,
            "curRightColor": [self.currentRightRed, self.currentRightGreen, self.currentRightBlue],
            "curLeftColor": [self.currentLeftRed, self.currentLeftGreen, self.currentLeftBlue],
        }

    # --- MQTT Callbacks ---
    def receive_commands(self, client, userdata, message):
        payload = json.loads(message.payload.decode())

        if payload.get("setRightColor"):
            self.update_right_color(payload.get("setRightColor"))
        elif payload.get("setLeftColor"):
            self.update_left_color(payload.get("setLeftColor"))
        elif payload.get("setCollectInterval"):
            self.update_collect_interval(payload.get("setCollectInterval"))

    def update_right_color(self, rightColor):
        logging.info(f"Updating {self.sensor_id} Right Color | Color: {rightColor}")
        self.setRightRed = rightColor[0]
        self.setRightGreen = rightColor[1]
        self.setRightBlue = rightColor[2]
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_setRightRed", str(self.setRightRed))
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_setRightGreen", str(self.setRightGreen))
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_setRightBlue", str(self.setRightBlue))

        message = {
            "sr-red": self.setRightRed,
            "sr-green": self.setRightGreen,
            "sr-blue": self.setRightBlue, 
            "setRightColor_info": f"Updated Right Color to RGB {self.setRightRed},{self.setRightGreen},{self.setRightBlue}",
            "setRightColor_status": "OK",
        }
        logging.debug(message)
        self.mqtt_client.publish(self.attrs_topic, json.dumps(message))

    def update_left_color(self, leftColor):
        logging.info(f"Updating {self.sensor_id} Left Color | Color: {leftColor}")
        self.setLeftRed = leftColor[0]
        self.setLeftGreen = leftColor[1]
        self.setLeftBlue = leftColor[2]
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_setLeftRed", str(self.setLeftRed))
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_setLeftGreen", str(self.setLeftGreen))
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_setLeftBlue", str(self.setLeftBlue))

        message = {
            "sl-red": self.setLeftRed,
            "sl-green": self.setLeftGreen,
            "sl-blue": self.setLeftBlue,
            "setLeftColor_info": f"Updated Left Color to RGB {self.setLeftRed},{self.setLeftGreen},{self.setLeftBlue}",
            "setLeftColor_status": "OK",
        }
        logging.info(message)
        self.mqtt_client.publish(self.attrs_topic, json.dumps(message))
        
    def update_collect_interval(self, collectInterval):
        logging.info(f"Updating {self.sensor_id} Collect Interval | Collect Interval: {collectInterval}")
        self.collectInterval = collectInterval
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_collectInterval", str(self.collectInterval))

        message = {
            "collectInterval": self.collectInterval,
            "collectInterval_info": f"Updated Collect Interval to {self.collectInterval}",
            "collectInterval_status": "OK",
        }
        logging.info(message)
        self.mqtt_client.publish(self.attrs_topic, json.dumps(message))

    # --- Utility functions ---
    def is_between(self):
        start_time = datetime.datetime.strptime(self.startTime, "%H:%M:%S").time()
        end_time = datetime.datetime.strptime(self.endTime, "%H:%M:%S").time()
        now = datetime.datetime.now().time()
        logging.debug(f"{start_time},{end_time},{now}")
        if start_time < end_time:
            return start_time <= now <= end_time
        else:
            return start_time <= now or now <= end_time

    def update_current_color(self):
        if self.is_between():
            self.currentRightRed = self.setRightRed
            self.currentRightGreen = self.setRightGreen
            self.currentRightBlue = self.setRightBlue
            self.currentLeftRed = self.setLeftRed
            self.currentLeftGreen = self.setLeftGreen
            self.currentLeftBlue = self.setLeftBlue
        else:
            self.currentRightRed = 0
            self.currentRightGreen = 0
            self.currentRightBlue = 0
            self.currentLeftRed = 0
            self.currentLeftGreen = 0
            self.currentLeftBlue = 0

    # --- Main device functions ---
    def actuate(self):
        logging.debug(f"Actuating {self.sensor_id}")
        
        for i in range(self.right_start, self.right_end):
            self.strip.setPixelColor(i, Color(self.currentRightRed, self.currentRightGreen, self.currentRightBlue))
        for i in range(self.left_start, self.left_end):
            self.strip.setPixelColor(i, Color(self.currentLeftRed, self.currentLeftGreen, self.currentLeftBlue))
            
        self.strip.show()

        message = {
            "cr-red": self.currentRightRed,
            "cr-green": self.currentRightGreen,
            "cr-blue": self.currentRightBlue,
            "cl-red": self.currentLeftRed,
            "cl-green": self.currentLeftGreen,
            "cl-blue": self.currentLeftBlue,
        }
        self.mqtt_client.publish(self.attrs_topic, json.dumps(message))

    def save_data(self):
        logging.debug(f"Saving data to sqlite {self.sensor_id}")
        # Create table
        try:
            conn = sqlite3.connect("/home/lab/Desktop/rasp-top/data-top.db")
            cur = conn.cursor()
            table_name = f"`{self.sensor_id}`"
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    currentRightRed INTEGER,
                    currentRightGreen INTEGER,
                    currentRightBlue INTEGER,
                    currentLeftRed INTEGER,
                    currentLeftGreen INTEGER,
                    currentLeftBlue INTEGER
                )
                """
            )
            cur.execute(
                f"INSERT INTO {table_name} (currentRightRed,currentRightGreen,currentRightBlue,currentLeftRed,currentLeftGreen,currentLeftBlue) VALUES (?,?,?,?,?,?)",
                (
                    self.currentRightRed,
                    self.currentRightGreen,
                    self.currentRightBlue,
                    self.currentLeftRed,
                    self.currentLeftGreen,
                    self.currentLeftBlue,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Device: {self.sensor_id} | Save to SQL | Error: {e}")

    def send_data(self):
        logging.debug(f"Sending data to MQTT broker {self.sensor_id}")
        data = {
            "cr-red": self.currentRightRed,
            "cr-green": self.currentRightGreen,
            "cr-blue": self.currentRightBlue,
            "cl-red": self.currentLeftRed,
            "cl-green": self.currentLeftGreen,
            "cl-blue": self.currentLeftBlue,
        }
        payload = json.dumps(data)
        self.mqtt_client.publish(self.attrs_topic, payload)

    # --- Main Loop ---
    def run(self):
        while True:
            self.update_current_color()
            self.actuate()
            self.save_data()
            self.send_data()
            logging.info(f"Fixture object: {self.__dir__()}")
            time.sleep(self.collectInterval)