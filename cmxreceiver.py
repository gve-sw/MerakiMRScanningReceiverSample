"""
Copyright (c) 2019 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

# code pulls cmx data from Meraki access point and saves in cmxData.csv file
# Libraries
from pprint import pprint
from flask import Flask
from flask import json
from flask import request
import sys, getopt
from datetime import datetime
import csv
import shutil
import json, requests
from config import ORG_ID, MERAKI_API_KEY, validator

############## USER DEFINED SETTINGS ###############
# MERAKI SETTINGS
secret = ""
version = "2.0" # This code was written to support the CMX JSON version specified
csvfile = None
devicesMapper={}
apNames={}


# gets meraki devices
def getDevices(network):
    # Get video link
    url = "https://api.meraki.com/api/v0/networks/"+network+"/devices/"

    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"""
    }
    resp = requests.request("GET", url, headers=headers)
    # print(resp)
    if int(resp.status_code / 100) == 2:
        return(resp.text)
    return('link error')

def getNetworks():
    url = "https://api.meraki.com/api/v0/organizations/" + ORG_ID + "/networks/"
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        "Content-Type": "application/json"""
    }
    resp = requests.request("GET", url, headers=headers)
    # print(resp)
    if int(resp.status_code / 100) == 2:
        return (resp.text)
    return ('link error')


# Save CMX Data for Recepcion
def save_data(data):
    # CHANGE ME - send 'data' to a database or storage system
    #pprint(data, indent=1)
    global csvfile
    global devicesMapper
    print("---- SAVING CMX DATA ----")
    print(data)
    for observation in data['data']['observations']:
        fieldnames = ['NETNAME','APNAME','APMAC','MAC', 'time', 'rssi']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'NETNAME':devicesMapper[data['data']['apMac']],'APNAME':apNames[data['data']['apMac']],'APMAC':data['data']['apMac'],'MAC': observation['clientMac'], 'time': observation['seenEpoch'], 'rssi': observation['rssi']})
    print("--- CMX DATA SAVED ---")




####################################################
app = Flask(__name__)

# Respond to Meraki with validator
@app.route('/', methods=['GET'])
def get_validator():
    print("validator sent to: ",request.environ['REMOTE_ADDR'])
    return validator

# Accept CMX JSON POST
@app.route('/', methods=['POST'])
def get_cmxJSON():
    if not request.json or not 'data' in request.json:
        return("invalid data",400)
    cmxdata = request.json
    #pprint(cmxdata, indent=1)
    print("Received POST from ",request.environ['REMOTE_ADDR'])

    # Verify secret
    if cmxdata['secret'] != secret:
        print("secret invalid:", cmxdata['secret'])
        return("invalid secret",403)
    else:
        print("secret verified: ", cmxdata['secret'])

    # Verify version
    if cmxdata['version'] != version:
        print("invalid version")
        return("invalid version",400)
    else:
        print("version verified: ", cmxdata['version'])

    # Determine device type
    if cmxdata['type'] == "DevicesSeen":
        print("WiFi Devices Seen")
        print(cmxdata['data']['apMac'])
        print(cmxdata)
        save_data(cmxdata)
    elif cmxdata['type'] == "BluetoothDevicesSeen":
        print("Bluetooth Devices Seen")
    else:
        print("Unknown Device 'type'")
        return("invalid device type",403)

    # Return success message
    return "CMX POST Received"


# Launch application with supplied arguments
def main(argv):
    global validator
    global secret
    global csvfile

    try:
       opts, args = getopt.getopt(argv,"hv:s:",["validator=","secret="])
    except getopt.GetoptError:
       print ('cmxreceiver.py -v <validator> -s <secret>')
       sys.exit(2)
    for opt, arg in opts:
       if opt == '-h':
           print ('cmxreceiver.py -v <validator> -s <secret>')
           sys.exit()
       elif opt in ("-v", "--validator"):
           validator = arg
       elif opt in ("-s", "--secret"):
           secret = arg
    print ('validator: '+validator)
    print ('secret: '+secret)
    print('Opening file to write out data...')

    #open the file to store the raw data
    csvfile=open('cmxData.csv', 'wt')

    #retrieve all networks from an org
    devices_data=getNetworks()
    theNetworks=json.loads(devices_data)

    #retrieve all access points from all networks to map them in memory to their corresponding network and device name
    for network in theNetworks:
        devices_data=getDevices(network['id'])
        theDevices = json.loads(devices_data)
        for device in theDevices:
            if device['model'][:2]=='MR':
                devicesMapper[device['mac']]=network['name']
                apNames[device['mac']]=device['name']

    print(devicesMapper)
    print(apNames)


if __name__ == '__main__':
    main(sys.argv[1:])
    app.run(port=5000,debug=False)
