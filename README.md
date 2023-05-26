## gardena-2-mqtt-domoticz
Python script to status, battery and connectivity data from Gardena Smart System using MQTT to Domoticz (or any other MQTT) 
Tested this on Gardena Sileno City, but should work on all Gardena/Husqvarna mowers

## Preconfig
* [Setup Domoticz with MQTT server](https://www.domoticz.com/wiki/MQTT)
* [Install Python3 on your Domoticz server](https://www.domoticz.com/wiki/Using_Python_plugins)

## Configuration to get Gardena/Husqvarna mower data 
* [Create account for Gardena API and generate API Key](https://developer.husqvarnagroup.cloud/)
  * Create new Application
  * Choose a name and a redirect URL as you like
  * Note Application Key
  * Note Application Secret
  * Add the Authentication API and the Gardena API to the application
* Create 3 dummy devices in Domoticz:
  * Battery: Percentage (DOMOTICZ_MOWER_RFLINK_IDX)
  * Status: Alert (DOMOTICZ_MOWER_STATUS_IDX)
  * Connectivity: Percentage (DOMOTICZ_MOWER_RFLINK_IDX)
* Edit the domoticz.cfg and edit the variables listed, make sure the MQTT is pointing to the right IP/URL (default: Localhost). 
* Run the script:  ```python3 gardena.py```
* Check if the dummy devices receive the correct values, if not, make sure your variables are all set correctly and all python addons are installed. ```python3 -m pip install MODULNAME```

## Configuration for Gardena mower control
* Create a dummy devices in Domoticz:
    *   Select button: Robot Action
* Edit the button action in Domoticz with On/Off action  ```script:///gardena/mower_control.sh "INSERT ACTION KEY HERE" ``` 
    * Fill in the action key based on button (for example: ```script:///gardena/mower_control.sh "START_DONT_OVERRIDE" ```):    
        * START_SECONDS_TO_OVERRIDE - Manual operation add the time in seconds as second attribute.
        * START_DONT_OVERRIDE - Automatic operation.
        * PARK_UNTIL_NEXT_TASK - Cancel the current operation and return to charging station.
        * PARK_UNTIL_FURTHER_NOTICE - Cancel the current operation, return to charging station, ignore schedule.

## Auto startup
* Edit the gardena.service file to the current paths.
* Copy the file to the service folder (e.g.: ```sudo cp gardena.service /lib/systemd/system/``` )
* Reload the Service Daemon (```sudo systemctl daemon-reload``` )
* Start the Service (```sudo systemctl enable gardena```)
* Check Status / Start / Stop or Restart with ```sudo service gardena status|start|stop|restart```

## Forked
This is a forke from https://github.com/Kdonkers/domoticz-mqtt2-gardena

