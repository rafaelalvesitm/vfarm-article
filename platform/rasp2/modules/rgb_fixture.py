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

# from lib.mqtt_client import MqttClient

from rpi_ws281x import Adafruit_NeoPixel, Color, ws


class LightFixture():
    def __init__(self, mqtt_client, sensor_key, sensor_id):
        # --- Set environement file --- 
        self.dotenv_file = "/home/lab/Desktop/rasp-bottom/.env"
        
        # --- Sensor Attributes ---
        self.sensor_key = sensor_key  # API Key from IoT Agent JSON
        self.sensor_id = sensor_id  # API Key from IoT Agent JSON

        # Sensor Attributes as defined in the IoT Agent JSON
        self.startTime = os.environ.get(f"{self.sensor_id}_startTime", "10:00:00")
        self.endTime = os.environ.get(f"{self.sensor_id}_endTime", "20:00:00")
        self.setRightRed = int(os.environ.get(f"{self.sensor_id}_setRightRed", "255"))
        self.setRightGreen = int(os.environ.get(f"{self.sensor_id}_setRightGreen", "255"))
        self.setRightBlue = int(os.environ.get(f"{self.sensor_id}_setRightBlue", "255"))
        self.setLeftRed = int(os.environ.get(f"{self.sensor_id}_setLeftRed", "255"))
        self.setLeftGreen = int(os.environ.get(f"{self.sensor_id}_setLeftGreen", "255"))
        self.setLeftBlue = int(os.environ.get(f"{self.sensor_id}_setLeftBlue", "255"))
        self.curRightRed = int(os.environ.get(f"{self.sensor_id}_curRightRed", "0"))
        self.curRightGreen = int(os.environ.get(f"{self.sensor_id}_curRightGreen", "0"))
        self.curRightBlue = int(os.environ.get(f"{self.sensor_id}_curRightBlue", "0"))
        self.curLeftRed = int(os.environ.get(f"{self.sensor_id}_curLeftRed", "0"))
        self.curLeftGreen = int(os.environ.get(f"{self.sensor_id}_curLeftGreen", "0"))
        self.curLeftBlue = int(os.environ.get(f"{self.sensor_id}_curLeftBlue", "0"))
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

        # --- MQTT Client ---
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
            "startTime": self.startTime,
            "endTime": self.endTime,
            "RightColor": [self.curRightRed, self.curRightGreen, self.curRightBlue],
            "LeftColor": [self.curLeftRed, self.curLeftGreen, self.curLeftBlue],
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
            "setRightColor_info": "Updated Right Color",
            "setRightColor_status": "Ok",
        }
        logging.info(message)
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
            "setLeftColor_info": "Updated Left Color",
            "setLeftColor_status": "OK",
        }
        logging.info(message)
        self.mqtt_client.publish(self.attrs_topic, json.dumps(message))
        
    def update_collect_interval(self, collectInterval):
        logging.info(f"Updating {self.sensor_id} Collect Interval | Interval: {collectInterval}")
        self.collectInterval = collectInterval
        dotenv.set_key(self.dotenv_file, f"{self.sensor_id}_collectInterval", str(self.collectInterval))

        message = {
            "setCollectInterval": self.collectInterval,
            "setCollectInterval_info": "Updated Collect Interval",
            "setCollectInterval_status": "OK",
        }
        logging.info(message)
        self.mqtt_client.publish(self.attrs_topic, json.dumps(message))

    # --- Utility functions ---
    def is_between(self):
        start_time = datetime.datetime.strptime(self.startTime, "%H:%M:%S").time()
        end_time = datetime.datetime.strptime(self.endTime, "%H:%M:%S").time()
        now = datetime.datetime.now().time()
        if start_time < end_time:
            return start_time <= now <= end_time
        else:
            return start_time <= now or now <= end_time

    def update_current_color(self):
        if self.is_between():
            self.curRightRed = self.setRightRed
            self.curRightGreen = self.setRightGreen
            self.curRightBlue = self.setRightBlue
            self.curLeftRed = self.setLeftRed
            self.curLeftGreen = self.setLeftGreen
            self.curLeftBlue = self.setLeftBlue
        else:
            self.curRightRed = 0
            self.curRightGreen = 0
            self.curRightBlue = 0
            self.curLeftRed = 0
            self.curLeftGreen = 0
            self.curLeftBlue = 0

    # --- Main device functions ---
    def actuate(self):
        logging.debug(f"Actuating {self.sensor_id}")
        
        for i in range(self.right_start, self.right_end):
            self.strip.setPixelColor(i, Color(self.curRightRed, self.curRightGreen, self.curRightBlue))
        for i in range(self.left_start, self.left_end):
            self.strip.setPixelColor(i, Color(self.curLeftRed, self.curLeftGreen, self.curLeftBlue))
            
        self.strip.show()

        message = {
            "cr-red": self.curRightRed,
            "cr-green": self.curRightGreen,
            "cr-blue": self.curRightBlue,
            "cl-red": self.curLeftRed,
            "cl-green": self.curLeftGreen,
            "cl-blue": self.curLeftBlue,
        }
        self.mqtt_client.publish(self.attrs_topic, json.dumps(message))

    def save_data(self):
        logging.debug(f"Saving data to sqlite {self.sensor_id}")
        # Create table
        try:
            conn = sqlite3.connect("/home/lab/Desktop/rasp-bottom/data-bottom.db")
            cur = conn.cursor()
            table_name = f"`{self.sensor_id}`"
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    curRightRed INTEGER,
                    curRightGreen INTEGER,
                    curRightBlue INTEGER,
                    curLeftRed INTEGER,
                    curLeftGreen INTEGER,
                    curLeftBlue INTEGER
                )
                """
            )
            cur.execute(
                f"INSERT INTO {table_name} (curRightRed,curRightGreen,curRightBlue,curLeftRed,curLeftGreen,curLeftBlue) VALUES (?,?,?,?,?,?)",
                (
                    self.curRightRed,
                    self.curRightGreen,
                    self.curRightBlue,
                    self.curLeftRed,
                    self.curLeftGreen,
                    self.curLeftBlue,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Device: {self.sensor_id} | Save to SQL | Error: {e}")

    def send_data(self):
        logging.debug(f"Sending data to MQTT broker {self.sensor_id}")
        data = {
            "cr-red": self.curRightRed,
            "cr-green": self.curRightGreen,
            "cr-blue": self.curRightBlue,
            "cl-red": self.curLeftRed,
            "cl-green": self.curLeftGreen,
            "cl-blue": self.curLeftBlue,
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