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

# code pulls cmx observation data from the CMXData.csv file and creates a summary of visits
# in CMXSummary.csv
# Libraries

from datetime import datetime
from pytz import timezone
import csv
from config import initialRSSIThreshold, visitorRSSIThreshold, maxSecondsAwayNewVisit, minMinutesVisit, theTimeZone

csvinputfile = None
csvoutputfile = None


if __name__ == '__main__':
    theObservations={}
    fieldnamesin = ['NETNAME', 'APNAME', 'APMAC', 'MAC', 'time', 'rssi']

    with open('cmxData.csv', newline='') as csvinputfile:
        datareader = csv.DictReader(csvinputfile, fieldnames=fieldnamesin)
        for row in datareader:
            #print(row['NETNAME'], row['APNAME'],row['APMAC'], row['MAC'], row['time'], row['rssi'])
            #assigning client MAC address from the row from the input file to a separate variable for better
            #readability of the code
            newMAC=row['MAC']
            #first check to see if we have seen this potential visitor
            if newMAC in theObservations:
                # if we have seen it, check to see if this record is from a different AP at the same time
                if theObservations[newMAC]['latest_ts']==int(row['time']):
                    #if so, assign the largest RSSI to the data structure we keep in memory so we do not make a decision
                    #about the end of a visit based on an API that is not the one closest to the visitor
                    theObservations[newMAC]['latest_rssi']=max(int(row['rssi']),theObservations[newMAC]['latest_rssi'])
                else:
                    # if not the same, there is a new timestamp for the same unique client ID, so we must update the
                    # latest_ts and latest_rssi fields, but only if above the rssi threshold to still consider a visitor
                    # and the new timestamp cannot be more than maxSecondsAwayNewVisit from the latest recorded
                    if int(row['rssi'])>=visitorRSSIThreshold and (int(row['time'])-theObservations[newMAC]['latest_ts'])<=maxSecondsAwayNewVisit:
                        theObservations[newMAC]['latest_ts'] = int(row['time'])
                        theObservations[newMAC]['latest_rssi'] = int(row['rssi'])
            else:
                #if we have not seen it , time to create a new entry if the RSSI is larger than initialRSSIThreshold
                if int(row['rssi'])>=initialRSSIThreshold:
                    theObservations[newMAC]={}
                    theObservations[newMAC]['first_ts']=int(row['time'])
                    theObservations[newMAC]['latest_ts'] = int(row['time'])
                    theObservations[newMAC]['latest_rssi'] = int(row['rssi'])
                    theObservations[newMAC]['netname'] = row['NETNAME']

    print("Done reading and mapping, starting to generate summary file...")

    fieldnamesout = ['NETNAME', 'MAC', 'date', 'time', 'length']
    with open('cmxSummary.csv', 'w', newline='') as csvoutputfile:
        localTZ = timezone(theTimeZone)
        writer = csv.DictWriter(csvoutputfile, fieldnames=fieldnamesout)
        for theKey in theObservations:
            theTime=datetime.fromtimestamp(theObservations[theKey]['first_ts'])
            theLocalTime=theTime.astimezone(localTZ)
            theDeltaSeconds=theObservations[theKey]['latest_ts']-theObservations[theKey]['first_ts']
            theVisitLength=round(theDeltaSeconds / 60,2)
            if theVisitLength>=minMinutesVisit:
                writer.writerow({'NETNAME': theObservations[theKey]['netname'],
                                 'MAC': theKey,
                                 'date': theLocalTime.strftime('%m/%d/%Y'),
                                 'time': theLocalTime.strftime('%H:%M'),
                                 'length': theVisitLength})

    print("Summary File generated.")


