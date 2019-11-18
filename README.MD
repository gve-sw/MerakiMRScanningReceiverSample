# Meraki MR Analytics Telemetry receiver demo

These python scripts recieve telemetry from the Meraki Scanning API and stores it in plain text
using CSV format in the cmxData.csv file. It also generates a list of "visits" based on WiFi enabled devices detected
entering and leaving the area covered by the MR access points and stores it in a file named cmxSummary.csv
<br/>
This information can be used to build a much more customized variant of the Meraki Dashboard Analytics reports for location
since it can be fed into solutions like Tableau for detailed processing.
<br/>
To be able to calculates visits, the application stores the following for each "observation" it receives (one row per observation)
in a file named 'cmxData.csv':
<br/>
```Network Name, Access Point Name, Access Point MAC, Client MAC, Timestamp, RSSI```
<br/>
The **Network Name** and **Access Point Name** are retrieved when when script first runs since it creates a map of all MR devices from all networks
in the organization defined in the ORG_ID variable in the config.py file.
<br/>
More details on the Access Point MAC, Client MAC, Timestamp and RSSI fields can be found here:
https://developer.cisco.com/meraki/scanning-api/#!api-version-2-0/wifi-devices
<br/>
The 'cmxSummary.csv' file, which gets generated after running the cmxsummary.py script, contains the following for each row:
<br/>
```Network Name, Client MAC, Visit Date (timezone adjusted), Visit Time (timezone adjusted), Visit Length (minutes)```
<br/>
What constitutes a "visit" is determined by an algorithm that uses the initialRSSIThreshold, visitorRSSIThreshold, maxSecondsAwayNewVisit,
minMinutesVisit and theTimeZone variables as follows:
<br/>
<br/>
**initialRSSIThreshold**: RSSI (wifi signal strengh) value to test for before registering the start of a visit. The suggested value is 15 which is what
is used by Meraki for the location analytics reports in the Dashboard<br/>
**visitorRSSIThreshold**: RSSI (wifi signal strengh) value to test for to consider if a device is still within the premises. The suggested value is 10 which is what
is used by Meraki for the location analytics reports in the Dashboard<br/>
**maxSecondsAwayNewVisit**: Number of seconds to tolerate that a device being tracked as part of a visit is not included in any observation from any of the access points in a network.
We suggest 120 seconds just to give chance in case one "observations" report is not succesfully send and received <br/>
**minMinutesVisit**: Number of minutes that a visitor's device is seen to record an actual visit to the premises. A value of 5 seconds is adequate for many retail situations
but really depends on the nature of the business.<br/>
**theTimeZone**: Timezone to use when generating the timestams in the cmxSummary.csv output file<br/>

---
## Configuration

**Config.py** contains all of the global variables and configuration needed throughout the code, including keys and thresholds such as initialRSSIThreshold, visitorRSSIThreshold, maxSecondsAwayNewVisit,
minMinutesVisit and theTimeZone.

In that file, you must fill in the values for the following variables:

MERAKI_API_KEY: This should contain your Meraki API key (details at https://developer.cisco.com/meraki/scanning-api/#!enable-scanning-api/enable-scanning-api)
ORG_ID: This is the Organization ID you wish to use from which to consider all encompassing networks to search for cameras.
validator: This string is used to have a way to match the process implementing the webhook with what is configured in the dashboard.


---
## CMX Access point Setup
Cisco Meraki CMX Receiver is a simple example demonstrating how to interact with the CMX API.
How it works:
- Meraki access points will listen for WiFi clients that are searching for a network to join and log the events.
- The "observations" are then collected temporarily in the cloud where additional information can be added to
the event, such as GPS, X Y coordinates and additional client details.
- Meraki will first send a GET request to this CMX receiver, which expects to receive a "validator" key that matches
the Meraki network's validator.
- Meraki will then send a JSON message to this application's POST URL (i.e. http://yourserver/ method=[POST])
- The JSON is checked to ensure it matches the expected secret, version and observation device type.
- The resulting data is sent to the "save_data(data)" function where it can be sent to a database or other service
Default port: 5000

Cisco Meraki CMX Documentation
https://documentation.meraki.com/MR/Monitoring_and_Reporting/CMX_Analytics#CMX_Location_API

---
## CMX Configuration

1. In the config.py file, there is a section for “Variables utilized in cmxreceiver.py” which contains all of the config variables for the cmx data gathering code
2. Validator is the validator key that can be found in the Meraki dashboard by navigating to **Network-wide > General
3. Scroll down to “Location and Analytics” to copy and paste this validator key into code (ensure analytics and scanning API are enabled)
4. _RSSI_THRESHOLD is the minimum rssi value needed for a device to be written into database (rssi is the signal strength of the device seen by the access point
5. _APMACADDR is the MAC address of the desired access point to gather data from

---
## Access Point setting

1. Download ngrok which is used to create public URLs for programs (more information here: https://ngrok.com)
2. Use ngrok to expose port 5000 by entering ‘./ngrok http 5000’ into terminal
3. You should see a url created that looks similar to this ‘https://2a6eed03.ngrok.io/'
4. Copy and paste this url into the “Post URL” section of “Location and Analytics” in the Meraki Dashboard
5. Note that the validate button should fail at this point as the the cmx receiver is not up and running

More details on configuring the Meraki Dashboard for the Scanning API can be found here:
https://developer.cisco.com/meraki/scanning-api/#!enable-scanning-api/enable-scanning-api


---
 ## Running Code

1. Make sure Python is installed
2. Make sure pip is installed (https://pip.pypa.io/en/stable/installing/ for more information on pip)
3. Enter 'pip install -r requirements.txt' into command line to download necessary libraries
4. Ensure all elements of the config.py file are completed
5. Ensure ngrok is running and that the url matches what is in the Meraki Dashboard (./ngrok http 5000)
6. In a new terminal window, enter ‘python3 cmxreceiver.py’ (note at this point the validate button in the Meraki dashboard should be working, data will stream every minute or so)
7. Once you are done collecting observations with the cmxreceiver.py script or while collecting, you can run the cmxsummary.py script to generate
the list of unique visitors in cmxSummary.csv. To run it, enter ‘python3 cmxsummary.py’ in the command line.