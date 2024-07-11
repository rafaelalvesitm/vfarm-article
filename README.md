# Article

This work has been submitted to the journal "Applied Soft Computing" as of 12 of July, 2024. 

# How this repository works? 

This repository contains the files used to define the IoT Platform (platform forlder), both Rasoberry Pi, the Genetic Algorithm and data collected and presented in the article. 

**It is crucial to note that parts of the code are hard coded**. While this is not ideal for sharing the code publicly, it facilitates the deployment in the real system used in the proposed work. 

## IoT Platform

The Internet of Things platform used in this project is based on FIWARE Generic Enablers. The platform was developed using Docker technology and can run on any operating system that supports Docker technology.

The components used in the platform are:

- [Orion Context Broker](https://fiware-orion.readthedocs.io/en/master/) - Context broker and main component of FIWARE;
- [Cygnus](https://fiware-cygnus.readthedocs.io/en/latest/) - Component to persist ontext data into SQL databases;
- [IoT Agent JSON](https://fiware-iotagent-json.readthedocs.io/en/latest/) - IoT Agent to convert JSON to NGSI protocol;
- [Mosquitto MQTT Broker](https://mosquitto.org/) - MQTT Broker for communication between IoT Agent JSON and IoT devices;
- [MongoDB](https://www.mongodb.com/) - NoSQL database;
- [MySQL](https://www.mysql.com/) - Relational database;
- [Grafana](https://grafana.com/) - Data visualization tool;

## Genetic Algorithm

The Genetic Algorithm is defined in the "geneticAlgorithm" folder as a Jupyter Notebook file. This was used to facilitate the operation of the algorithm with manual data collected from the growth tower. 

## Raspberry Pi

There are two folders for the Raspberry Pi used in the work. Each on has a collection of sensors and actuators described ussing Object-oriented programming. This programming method was used to allow users to easily replicate the code and to scale the solution in the future. 

## Collected data

The collected data is presented as an excel file in the folder "collectedData". 