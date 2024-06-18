"""
Author: Rafael Gomes Alves
Description: This script uses an object oriented programming to define a MQTT client.
"""

import paho.mqtt.client as mqtt
import logging
import os
import time

class MqttClient:
    def __init__(self):
        # Create a MQTT client
        self.client = mqtt.Client()
        self.broker_address = os.environ.get("BROKER_HOST")
        self.port = int(os.environ.get("BROKER_PORT"))
        
        print(f"{self.broker_address} and {self.port}")
        self.connected = False
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            self.connected = True
        else:
            print(f"Connection failed with code {rc}")
            self.connected = False
            
    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT broker")
        self.connected = False

    def on_message(self, client, userdata, msg):
        logging.info(f"Topic: {msg.topic} | Payload: {msg.payload.decode()}")

    def connect(self):
        while not self.connected:
            try:
                print("Trying to connect to MQTT broker...")
                self.client.connect(self.broker_address, self.port, 60)
                self.client.loop_start()
                while not self.connected:
                    time.sleep(1)
            except Exception as e:
                print(f"Connection failed. Retrying... Error: {e}")
                time.sleep(5)

    def publish(self, topic, message):
        if self.connected:
            self.client.publish(topic, message)
        else:
            print("Not connected to the broker. Cannot publish message.")

    def subscribe(self, topic):
        self.client.subscribe(topic)
    
    def message_callback_add(self, topic, callback):
        self.client.message_callback_add(topic, callback)

    def disconnect(self):
        self.client.disconnect()
        self.client.loop_stop()
        
        