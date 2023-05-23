#!/usr/bin/env python
# v1.0 - 20230521 - Initial working Version for Domoticz
# v1.1 - 20230522 - Add nice looking Status Messages for Domoticz with Language Files
# v1.2 - 20230523 - Fix some Bugs when running as Service
import websocket
from threading import Thread
import time
import sys
import requests
import json
import paho.mqtt.client as mqtt
import configparser
import os
import datetime

# CONFIG
os.chdir(os.path.dirname(sys.argv[0]))
configParser = configparser.RawConfigParser()
configFilePath = r'./../domoticz.cfg'
configParser.read(configFilePath)

# API URLs
AUTHENTICATION_HOST = 'https://api.authentication.husqvarnagroup.dev'
SMART_HOST = 'https://api.smart.gardena.dev'

# account specific values
CLIENT_ID=configParser.get('Gardena', 'CLIENT_ID')
CLIENT_SECRET=configParser.get('Gardena', 'CLIENT_SECRET')
CLIENT_API_KEY=configParser.get('Gardena', 'API_KEY')
CLIENT_LANGUAGE=configParser.get('Gardena', 'CLIENT_LANGUAGE')

#MQTT
DOMOTICZ_TOPIC=configParser.get('MQTT', 'TOPIC')
DOMOTICZ_MOWER_STATUS_IDX=int(configParser.get('Gardena', 'MOWER_STATUS_IDX'))
DOMOTICZ_MOWER_BATTERY_IDX=int(configParser.get('Gardena', 'MOWER_BATTERY_IDX'))
DOMOTICZ_MOWER_RFLINK_IDX=int(configParser.get('Gardena', 'MOWER_RFLINK_IDX'))
DOMOTICZ_MQTT=configParser.get('MQTT', 'SERVER')
DOMOTICZ_USER_MQTT=configParser.get('MQTT', 'USERNAME')
DOMOTICZ_PASSWORD_MQTT=configParser.get('MQTT', 'PASSWORD')
DOMOTICZ_MQTT_PORT=int(configParser.get('MQTT', 'PORT'))

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(DOMOTICZ_USER_MQTT, DOMOTICZ_PASSWORD_MQTT)
mqtt_client.connect(DOMOTICZ_MQTT,DOMOTICZ_MQTT_PORT,60)
mqtt_client.loop_start()

class Client:
    def on_message(self, ws, message):
        x = datetime.datetime.now()
        print("API Message arrived ", x.strftime("%H:%M:%S,%f"))
        mqtt_parse(message)
        #print(message)     #Disabled print to reduce Log amount
        sys.stdout.flush()

    def on_error(self, ws, error):
        x = datetime.datetime.now()
        print("An error occurred ", x.strftime("%H:%M:%S,%f"))
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        self.live = False
        x = datetime.datetime.now()
        print("Connection closed ", x.strftime("%H:%M:%S,%f"))
        print("### closed ###")
        try:
            if close_status_code:
                print("status code: "+ str(close_status_code))
            if close_msg:
                print("status message: "+ close_msg)
        except:
            print("Error while closing the connection.")
        sys.exit(0)

    def on_open(self, ws):
        x = datetime.datetime.now()
        print("Connection established ", x.strftime("%H:%M:%S,%f"))
        print("### connected ###")

        self.live = True

        def run(*args):
            while self.live:
                time.sleep(1)

        Thread(target=run).start()

def mqtt_parse(message):
    response = json.loads(message)
    response_type = response['type']
    with open("./language.json") as txtfile:
        languagefile=json.loads(txtfile.read())

    # Types are DEVICE, LOCATION, COMMON and MOWER
    if response_type == 'MOWER':
        response_value = response['attributes']['activity']['value']
        title = languagefile['values'][response_value][CLIENT_LANGUAGE]
        # print(title)  # For Debug
        mqtt_client.publish(DOMOTICZ_TOPIC, json.dumps({'idx': DOMOTICZ_MOWER_STATUS_IDX, 'svalue': title}))
        
        # Default Request
        # mqtt_client.publish(DOMOTICZ_TOPIC, json.dumps({'idx': DOMOTICZ_MOWER_STATUS_IDX, 'svalue': response['attributes']['activity']['value']}))
    elif response_type == 'COMMON':
        mqtt_client.publish(DOMOTICZ_TOPIC, json.dumps({'idx': DOMOTICZ_MOWER_BATTERY_IDX, 'svalue': '{}%'.format(response['attributes']['batteryLevel']['value'])}))
        mqtt_client.publish(DOMOTICZ_TOPIC, json.dumps({'idx': DOMOTICZ_MOWER_RFLINK_IDX, 'svalue':  '{}%'.format(response['attributes']['rfLinkLevel']['value'])}))

if __name__ == "__main__":
    payload = {'grant_type': 'client_credentials', 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}

    print("Logging into authentication system...")
    r = requests.post('{}/v1/oauth2/token'.format(AUTHENTICATION_HOST), data=payload)
    assert r.status_code == 200, r
    auth_token = r.json()["access_token"]

    headers = {
        "Content-Type": "application/vnd.api+json",
        "x-api-key": CLIENT_API_KEY,
        "Authorization": "Bearer " + auth_token
    }

    r = requests.get('{}/v1/locations'.format(SMART_HOST), headers=headers)
    assert r.status_code == 200, r
    assert len(r.json()["data"]) > 0, 'location missing - user has not setup system'
    location_id = r.json()["data"][0]["id"]

    payload = {
        "data": {
            "type": "WEBSOCKET",
            "attributes": {
                "locationId": location_id
            },
            "id": "does-not-matter"
        }
    }
    print("Logged in (%s), getting WebSocket ID..." % auth_token)
    r = requests.post('{}/v1/websocket'.format(SMART_HOST), json=payload, headers=headers)

    assert r.status_code == 201, r
    print("WebSocket ID obtained, connecting...")
    response = r.json()
    websocket_url = response["data"]["attributes"]["url"]

    websocket.enableTrace(True)
    client = Client()
    ws = websocket.WebSocketApp(
        websocket_url,
        on_message=client.on_message,
        on_error=client.on_error,
        on_close=client.on_close)
    ws.on_open = client.on_open
    ws.run_forever(ping_interval=150, ping_timeout=1)
