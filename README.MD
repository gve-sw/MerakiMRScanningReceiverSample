# Meraki MX Analytics Telemetry receiver demo

This application receives telemetry from the Meraki Scanning API and stores it in plain text
using CSV format in the cmxData.csv file.

It stores the following for each "observation" it receives (one row per observation):

Network Name, Access Point Name, Access Point MAC, Client MAC, Timestamp, RSSI

More details on the Access Point MAC, Client MAC, Timestamp and RSSI fields can be found here:
https://developer.cisco.com/meraki/scanning-api/#!api-version-2-0/wifi-devices

The **Network Name** and **Access Point Name** are retrieved when when script first runs since it creates a map of all MR devices from all networks
in the organization defined in the ORG_ID variable in the config.py file.


## Configuration

**Config.py** contains all of the global variables and configuration needed throughout the code, including keys and thresholds.

——------ CMX Access point Setup ------——
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

—— CMX Configuration ——
1. In the config.py file, there is a section for “Variables utilized in cmxreceiver.py” which contains all of the config variables for the cmx data gathering code
2. Validator is the validator key that can be found in the Meraki dashboard by navigating to **Network-wide > General
3. Scroll down to “Location and Analytics” to copy and paste this validator key into code (ensure analytics and scanning API are enabled)
4. _RSSI_THRESHOLD is the minimum rssi value needed for a device to be written into database (rssi is the signal strength of the device seen by the access point
5. _APMACADDR is the MAC address of the desired access point to gather data from

—— Access Point setting ——
1. Download ngrok which is used to create public URLs for programs (more information here: https://ngrok.com)
2. Use ngrok to expose port 5000 by entering ‘./ngrok http 5000’ into terminal
3. You should see a url created that looks similar to this ‘https://2a6eed03.ngrok.io/'
4. Copy and paste this url into the “Post URL” section of “Location and Analytics” in the Meraki Dashboard
5. Note that the validate button should fail at this point as the the cmx receiver is not up and running

More details on conguring the Meraki Dashboard for the Scanning API can be found here:
https://developer.cisco.com/meraki/scanning-api/#!enable-scanning-api/enable-scanning-api



——------ Running Code ------—— 
1. Make sure Python is installed
2. Make sure pip is installed (https://pip.pypa.io/en/stable/installing/ for more information on pip)
3. Enter 'pip install -r requirements.txt' into command line to download necessary libraries
4. Ensure all elements of the config.py file are completed
5. Ensure ngrok is running and that the url matches what is in the Meraki Dashboard (./ngrok http 5000)
6. In a new terminal window, enter ‘python3 cmxreceiver.py’ (note at this point the validate button in the Meraki dashboard should be working, data will stream every minute or so)