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
import json, requests, os, time
from config import ORG_ID, MERAKI_API_KEY, validator

from pytz import timezone
from config import initialRSSIThreshold, visitorRSSIThreshold, maxSecondsAwayNewVisit, minMinutesVisit, theTimeZone, summaryTimePeriod

csvinputfile = None
csvoutputfile = None


############## USER DEFINED SETTINGS ###############
# MERAKI SETTINGS
secret = ""
version = "2.0" # This code was written to support the CMX JSON version specified
csvfile = None
devicesMapper={}
apNames={}

def setTimeTrackers():
    global dayTracker, hourTracker, monthTracker, testTracker, yearTracker
    tz = timezone(theTimeZone)
    theLocalTime = datetime.now(tz)
    yearTracker=theLocalTime.year
    monthTracker=theLocalTime.month
    dayTracker=theLocalTime.day
    hourTracker=theLocalTime.hour
    testTracker=int(theLocalTime.minute/10)

def generateSummaryFile(fileTS):

    theObservations = {}
    fieldnamesin = ['NETNAME', 'APNAME', 'APMAC', 'MAC', 'time', 'rssi']
    newFileName=fileTS+r'-cmxData.csv'
    os.rename(r'cmxData.csv',
              newFileName)
    with open(newFileName, newline='') as csvinputfile:
        datareader = csv.DictReader(csvinputfile, fieldnames=fieldnamesin)
        for row in datareader:
            # print(row['NETNAME'], row['APNAME'],row['APMAC'], row['MAC'], row['time'], row['rssi'])
            # assigning client MAC address from the row from the input file to a separate variable for better
            # readability of the code
            newMAC = row['MAC']
            # first check to see if we have seen this potential visitor
            if newMAC in theObservations:
                # if we have seen it, check to see if this record is from a different AP at the same time
                # focus on the latest visit from the visits array o the observation
                if theObservations[newMAC][-1]['latest_ts'] == int(row['time']):
                    # if so, assign the largest RSSI to the data structure we keep in memory so we do not make a decision
                    # about the end of a visit based on an API that is not the one closest to the visitor
                    theObservations[newMAC][-1]['latest_rssi'] = max(int(row['rssi']),
                                                                     theObservations[newMAC][-1]['latest_rssi'])
                else:
                    # if not the same, there is a new timestamp for the same unique client ID, so we must check against
                    # let latest visit in the array and update the
                    # latest_ts and latest_rssi fields, but only if above the rssi threshold to still consider a visitor
                    # and the new timestamp cannot be more than maxSecondsAwayNewVisit from the latest recorded
                    # if it is, then we have to add a new visit record to the array
                    if int(row['rssi']) >= visitorRSSIThreshold:
                        if (int(row['time']) - theObservations[newMAC][-1]['latest_ts']) <= maxSecondsAwayNewVisit:
                            theObservations[newMAC][-1]['latest_ts'] = int(row['time'])
                            theObservations[newMAC][-1]['latest_rssi'] = int(row['rssi'])
                        elif int(row['rssi']) >= initialRSSIThreshold:
                            # this is a new visit (also checked RSSI above new visti threshold), append new entry to
                            # the array of visits with all relevant values
                            newVisit = {}
                            newVisit['first_ts'] = int(row['time'])
                            newVisit['latest_ts'] = int(row['time'])
                            newVisit['latest_rssi'] = int(row['rssi'])
                            newVisit['netname'] = row['NETNAME']
                            theObservations[newMAC].append(newVisit)

            else:
                # if we have not seen it , time to create a visits array for that MAC if the RSSI is larger than initialRSSIThreshold
                if int(row['rssi']) >= initialRSSIThreshold:
                    theObservations[newMAC] = []
                    firstVisit = {}
                    firstVisit['first_ts'] = int(row['time'])
                    firstVisit['latest_ts'] = int(row['time'])
                    firstVisit['latest_rssi'] = int(row['rssi'])
                    firstVisit['netname'] = row['NETNAME']
                    theObservations[newMAC].append(firstVisit)

    csvinputfile.close()

# Data File Removal: comment out next 4 lines to retain detailed data files after summary generation
    if os.path.exists(newFileName):
        os.remove(newFileName)
    else:
        print("The "+newFileName+" data file does not exist.")

    print("Done reading and mapping, starting to generate summary file...")

    fieldnamesout = ['NETNAME', 'MAC', 'date', 'time', 'length']
    newSummaryFileName=fileTS+'-cmxSummary.csv'
    with open(newSummaryFileName, 'w', newline='') as csvoutputfile:
        localTZ = timezone(theTimeZone)
        writer = csv.DictWriter(csvoutputfile, fieldnames=fieldnamesout)
        for theKey in theObservations:
            for theVisitInstance in theObservations[theKey]:
                theTime = datetime.fromtimestamp(theVisitInstance['first_ts'])
                theLocalTime = theTime.astimezone(localTZ)
                theDeltaSeconds = theVisitInstance['latest_ts'] - theVisitInstance['first_ts']
                theVisitLength = round(theDeltaSeconds / 60, 2)
                if theVisitLength >= minMinutesVisit:
                    writer.writerow({'NETNAME': theVisitInstance['netname'],
                                     'MAC': theKey,
                                     'date': theLocalTime.strftime('%m/%d/%Y'),
                                     'time': theLocalTime.strftime('%H:%M'),
                                     'length': theVisitLength})
    csvoutputfile.close()
    print("Summary File generated.")


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
    global csvfile, dayTracker, hourTracker, monthTracker, testTracker, yearTracker
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

    fileTS=''
    if summaryTimePeriod!='M':
        # check to see if it is time to generate summary
        tz = timezone(theTimeZone)
        theLocalTime = datetime.now(tz)
        #based on the timePeriod we are testing for, generate the timeStamp for the summary file if the time has come
        if summaryTimePeriod=='D':
            if dayTracker!=theLocalTime.day:
                fileTS=str(yearTracker)+'-'+str(monthTracker).zfill(2)+'-'+str(dayTracker).zfill(2)
                setTimeTrackers()
        elif summaryTimePeriod=='H':
            if hourTracker!=theLocalTime.hour:
                fileTS=str(yearTracker)+'-'+str(monthTracker).zfill(2)+'-'+str(dayTracker).zfill(2)+"-"+str(hourTracker).zfill(2)
                setTimeTrackers()
        elif summaryTimePeriod=='T':
            if testTracker!=int(theLocalTime.minute/10):
                fileTS=str(yearTracker)+'-'+str(monthTracker).zfill(2)+'-'+str(dayTracker).zfill(2)+"-"+str(hourTracker).zfill(2)+str(testTracker)
                setTimeTrackers()
        #generate the summary and rename the old detailed file only if we are in new time period
        if fileTS!='':
            # close the detailed file
            csvfile.close()
            generateSummaryFile(fileTS)
            # re-open the file to store the raw data
            csvfile = open('cmxData.csv', 'wt')


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
    global dayTracker, hourTracker, testTracker, monthTracker, yearTracker

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
        time.sleep(0.25)
        theDevices = json.loads(devices_data)
        for device in theDevices:
            if device['model'][:2]=='MR':
                print("========> Here is the data for just one device: ", json.dumps(device, indent=4, sort_keys=True))
                devicesMapper[device['mac']]=network['name']
                apNames[device['mac']]=device['name']

    print(devicesMapper)
    print(apNames)
    #set the time periods where it starts to run to know when to do the summaries
    setTimeTrackers()
    print(testTracker)


if __name__ == '__main__':
    main(sys.argv[1:])
    app.run(port=5000,debug=False)
