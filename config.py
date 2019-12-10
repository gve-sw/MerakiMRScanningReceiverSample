# this config file contains multiple variables utilized throughout the functionality of this code
MERAKI_API_KEY = "YYYYYYYYYYYYYYYYYYYYYYY"
ORG_ID = "XXXXXXXX"
validator = "ZZZZZZZZZZZZZZ"

#these are the parameters and thresholds used by the cmxsummary.py script
initialRSSIThreshold=15
visitorRSSIThreshold=10
maxSecondsAwayNewVisit=120
minMinutesVisit=5
theTimeZone='US/Central'
#how long to wait until running summary: Daily='D', Hourly='H', Test='T' (10 min interval), Manual='M'
summaryTimePeriod='T'