# The Project
This is a research project developed at the [Centro Universitário FEI](https://portal.fei.edu.br/), located in São Bernardo do Campo/Brazil. 

## General Objective
The main objective of this project is to develop a Digital Twin of a cultivation tower using the Internet of Things and Artificial Intelligence as enabling technologies.

## Specific Objectives
The specific objectives are:

- Develop the physical structure of a cultivation tower;
- Develop a monitoring and control system for the cultivation tower using sensors, actuators, and microprocessors;
- Develop an Internet of Things platform to monitor, control, and manage the cultivation tower;
- Develop an Artificial Intelligence algorithm to manage and possibly optimize the operation of the cultivation tower.

## Team
- [Rafael Gomes Alves](https://www.rafaelalvesitm.com/) - PhD student in Electrical Engineering at Centro Universitário FEI;
- Prof. Dr. Salvador Pinillos Gimenez - Professor in the Department of Electrical Engineering at Centro Universitário FEI;
- Prof. Dr. Fábio Lima - Professor in the Department of Production Engineering at Centro Universitário FEI;

## Article
This repository contains files used for the article "<Article Name here>". 

# Project development

## Internet of Things Platform - Powered by FIWARE

The Internet of Things platform used in this project is based on FIWARE Generic Enablers. The platform was developed using Docker technology and can be run on any operating system that supports Docker technology. The components used in the platform are:

- [Orion Context Broker](https://fiware-orion.readthedocs.io/en/master/) - Context Broker;
- [Cygnus](https://fiware-cygnus.readthedocs.io/en/latest/) - Agent for persisting context data in external databases;
- [IoT Agent JSON](https://fiware-iotagent-json.readthedocs.io/en/latest/) - IoT Agent for converting the JSON protocol to NGSI;
- [Mosquitto MQTT Broker](https://mosquitto.org/documentation/) - MQTT broker for communication between the IoT Agent JSON and IoT devices;
- [MongoDB](https://www.mongodb.com/docs/) - NoSQL database;
- [MySQL](https://dev.mysql.com/doc/) - Relational database;
- [Grafana](https://grafana.com/docs/) - Data visualization tool;

### How to run the platform

The platform's components are described in the `docker-compose.yml` file inside the platform folder. To run the platform, you can use the `services.sh` file by running the folowwing commands:

```bash
sudo bash ./services start # Start the containers for each component
sudo bash ./services stop # Stop the containers for each component
```

## Devices

## Genetic Algorithm
