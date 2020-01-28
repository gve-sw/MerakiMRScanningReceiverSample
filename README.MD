# Meraki MR Analytics Telemetry receiver demo

These python scripts recieve telemetry from the Meraki Scanning API and stores it in plain text
using CSV format in the **cmxData.csv** file. It also generates a list of "visits" based on WiFi enabled devices detected
entering and leaving the area covered by the MR access points and stores it in a file named **cmxSummary.csv**
<br/>
<br/>
This information can be used to build a much more customized variant of the Meraki Dashboard Analytics reports for location
since it can be fed into solutions like Tableau for detailed processing.
<br/>
<br/>
To be able to calculates visits, the application stores the following for each "observation" it receives (one row per observation)
in a file named **cmxData.csv**:
<br/>
<br/>
```Network Name, Access Point Name, Access Point MAC, Client MAC, Timestamp, RSSI```
<br/>
<br/>
The **Network Name** and **Access Point Name** are retrieved when when script first runs since it creates a map of all MR devices from all networks
in the organization defined in the ORG_ID variable in the config.py file.
<br/>
<br/>
More details on the Access Point MAC, Client MAC, Timestamp and RSSI fields can be found here:
https://developer.cisco.com/meraki/scanning-api/#!api-version-2-0/wifi-devices
<br/>
<br/>
The **cmxSummary.csv** file, which gets generated after running the cmxsummary.py script (if in Manual mode, or periodically by the main cmxreceiver.py script if not), contains the following for each row:
<br/>
<br/>
```Network Name, Client MAC, Visit Date (timezone adjusted), Visit Time (timezone adjusted), Visit Length (minutes)```
<br/>
<br/>
What constitutes a "visit" is determined by an algorithm that uses the initialRSSIThreshold, visitorRSSIThreshold, maxSecondsAwayNewVisit,
minMinutesVisit and theTimeZone variables as follows:
<br/>
<br/>
**initialRSSIThreshold**: RSSI (wifi signal strengh) value to test for before registering the start of a visit. The suggested value is 15 which is what
is used by Meraki for the location analytics reports in the Dashboard<br/><br/>
**visitorRSSIThreshold**: RSSI (wifi signal strengh) value to test for to consider if a device is still within the premises. The suggested value is 10 which is what
is used by Meraki for the location analytics reports in the Dashboard<br/><br/>
**maxSecondsAwayNewVisit**: Number of seconds to tolerate that a device being tracked as part of a visit is not included in any observation from any of the access points in a network.
We suggest 120 seconds just to give chance in case one "observations" report is not succesfully send and received <br/><br/>
**minMinutesVisit**: Number of minutes that a visitor's device is seen to record an actual visit to the premises. A value of 5 minutes is adequate for many retail situations
but really depends on the nature of the business.<br/><br/>
**theTimeZone**: Timezone to use when generating the timestams in the **cmxSummary.csv** output file<br/><br/>

---
## Configuration

**Config.py** contains all of the global variables and configuration needed throughout the code, including keys and thresholds such as initialRSSIThreshold, visitorRSSIThreshold, maxSecondsAwayNewVisit,
minMinutesVisit and theTimeZone.
<br/><br/>
In that file, you must fill in the values for the following variables:
<br/><br/>
**MERAKI_API_KEY**: This should contain your Meraki API key (details at https://developer.cisco.com/meraki/scanning-api/#!enable-scanning-api/enable-scanning-api)<br/>
**ORG_ID**: This is the Organization ID you wish to use from which to consider all encompassing networks to search for cameras.<br/>
**validator**: The validator key that can be found in the Meraki dashboard by navigating to **Network-wide > General. Scroll down to “Location and Analytics” to copy and paste this validator key into code (ensure analytics and scanning API are enabled)<br/>

You can also change the value for **summaryTimePeriod** which controls how often the code generates a summary of visits: 
 Daily='D', Hourly='H', Test='T' (10 min interval), Manual='M' (you have to run cmxsummary.py manually to generate the summary if you configure it with this last option)


---
## Local machine configuration and Meraki CMX Access point Setup

This Meraki CMX receiver sample is a simple example demonstrating how to interact with the CMX API.<br/>
This is how it works:
- Meraki access points will listen for WiFi clients that are searching for a network to join and log the events.
- The "observations" are then collected temporarily in the cloud where additional information can be added to
the event, such as GPS, X Y coordinates and additional client details.
- Meraki will first send a GET request to this CMX receiver, which expects to receive a "validator" key that matches
the Meraki network's validator.
- Meraki will then send a JSON message to this application's POST URL (i.e. http://yourserver/ method=[POST])
- The JSON is checked to ensure it matches the expected secret, version and observation device type.

Cisco Meraki CMX Documentation
https://documentation.meraki.com/MR/Monitoring_and_Reporting/CMX_Analytics#CMX_Location_API

More details on configuring the Meraki Dashboard for the Scanning API can be found here:
https://developer.cisco.com/meraki/scanning-api/#!enable-scanning-api/enable-scanning-api

Specifically for this example, **cmxreceiver.py** python script implements a web server that needs to have a publicly addressable address so that it can
be configured as a webhook on the Meraki Dashboard API. If you wish to run it on a machine behind a corporate firewall such as a
PC or laptop connected to a corporate network you need to use a utility such as Ngrok to open a "pinhole" on the firewall to be able
to redirect traffic to the script. Not all organizations support the use of ngrok or other similar utilities and it is definitely not
recommended to use in a production environment. But for quick testing it can be quite useful. Here is how you use it:
<br/><br/>

1. Download ngrok which is used to create public URLs for programs (more information here: https://ngrok.com)
2. Use ngrok to expose port 5000 by entering ‘./ngrok http 5000’ into terminal
3. You should see a url created that looks similar to this ‘https://2a6eed03.ngrok.io/'
4. Copy and paste this url into the “Post URL” section of “Location and Analytics” in the Meraki Dashboard
5. Note that the validate button should fail at this point as the the cmx receiver is not up and running



---
## Running the scripts

1. Make sure Python 3 is installed
2. Make sure pip is installed (https://pip.pypa.io/en/stable/installing/ for more information on pip)
3. Enter ```pip install -r requirements.txt``` into command line to download necessary libraries
4. Ensure all elements of the **config.py** file are completed
5. If behind a corporate firewall and using ngrok, make sure ngrok is running and that the url matches what is in the Meraki Dashboard (```./ngrok http 5000```)
6. In a new terminal window, enter ```python3 cmxreceiver.py``` (note at this point the validate button in the Meraki dashboard should be working, data will stream every minute or so)
7. Once you are done collecting observations with the **cmxreceiver.py** script or while collecting, you can run the **cmxsummary.py** script to generate
the list of unique visitors in **cmxSummary.csv**. To run it, enter ```python3 cmxsummary.py``` in the command line.

### NOTE
Currently, if a device in a network does not have a name in the Dashboar, the script will error out during setup since it is depending on those to identify each device in the output file. Just make sure that all devices have names. In a future version we will use the device ID as the name if missing. 
