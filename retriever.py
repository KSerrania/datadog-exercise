from collections import Counter
from datetime import datetime

class Retriever():
    """Retriever class whose goal is to get a website's monitoring data and compute interesting metrics about it.
    It also has a method to track and warn about availability alerts.

    Attributes:
        URL (str): URL of the monitored website.
        influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.
        alertData (:obj:): Data about the current alert (if there is an alert going on).
            alertStatus (bool): Indicates if there is an alert going on.
            alertNumber (int): Number of the alert (used to reference alerts).
            alertTime (datetime.datetime): Start date of the current (or last) alert.

    """

    def __init__(self, URL, influxClient):
        """Sets the URL and influxDBClient as speficied in the parameters.
        Also initializes the alert data of the website.

        Args:
            URL (str): URL of the monitored website.
            influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.

        """
        self.URL = URL
        self.influxClient = influxClient
        self.alertData = {
            'alertStatus': False,
            'alertNumber': 0,
            'alertTime': datetime.now()
        }

    def getStats(self, minutes):
        """Retrieves data about the monitored website from the InfluxDB database.
        The data retrieved is only the data recorded during the last {minutes} minutes, minutes 

        Args:
            minutes (int): The number of minutes in the past over which data is retrieved.

        Returns:
            A tuple composed of :
                - a boolean (False if the is no data about the website for the specified timespan, True otherwise)
                - a dictionary containing interesting stats about the website for the specified timespan:
                    availability (float): The availability of the website.
                    statusCodes (collections.Counter): The counts of the different response codes from requests on the website.
                    avgLatency (float): The average ping response time.
                    minLatency (float): The minimum ping response time.
                    maxLatency (float): The maximum ping response time.
                    pingResponse (float): The percentage of ping requests which have been answered.

        """

        # We first query the database
        data = self.influxClient.query("SELECT latency, status FROM website_availability WHERE time > now() - {}m AND host = '{}'".format(minutes, self.URL)).raw
        # The raw data from the query is a dictionary object.
        # The interesting data (for us) is associated to the series key 
        if 'series' in data.keys():
            # If there is available data
            # data['series'] is an array whose only relevant element for us is the first
            # This element (data['series'][0] contains another dictionary
            # In the 'values' key of this dictionary, we can find an array whose first element is the time
            # and whose following elements are the elements we requested, in the order they were requested
            
            # We create an array containing all the (not None) latencies
            latencies = [elt[1] for elt in data['series'][0]['values'] if elt[1] is not None]

            # And we create a counter of status codes
            statusCodes = Counter([elt[2] if elt[2] is not None else 404 for elt in data['series'][0]['values']])
        else:
            # If there is no data available
            return False, {}

        # We then compute some interesting statistics
        n = sum(statusCodes.values())
        nLatencies = len(latencies)
        minLatency = min(latencies, default=float('inf'))
        maxLatency = max(latencies, default=float('inf'))
        try:
            avgLatency = sum(latencies) / nLatencies
        except:
            avgLatency = float('inf')

        pingResponse = nLatencies / n
        # We define here the availability as the percentage of status 200 (OK) responses
        availability = statusCodes[200] / n

        # And we return these stats in a dictionary
        return True, {
                'availability': availability,
                'statusCodes': statusCodes,
                'avgLatency': avgLatency,
                'minLatency': minLatency,
                'maxLatency': maxLatency,
                'pingResponse': pingResponse
                }
    
    def checkAlert(self):
        """Checks if an availability alert (or recovery) message should be sent.
        The check timespan is 2 minutes.

        Returns:
            A string detailing the current condition of the website
        """

        #TODO: Change output to data dictionary
        
        # We first retrieve the website's data on the last 2 minutes
        statusCodes = Counter([elt[1] for elt in self.influxClient.query("SELECT status FROM website_availability WHERE time > now() - 2m AND host = '{}'".format(self.URL)).raw['series'][0]['values']])
        n = sum(statusCodes.values())
        # We compute the site's availability
        availability = statusCodes[200] / n
        
        if self.alertData['alertStatus'] and availability >= 0.8:
            # If the website was in alert status but has recovered, we send a recovery signal
            self.alertData['alertStatus']  = False
            return "\n\033[92mWebsite {} recovered from alert {}. Availability={:.2%}, time={}\033[0m".format(self.URL, availability, str(datetime.now()))
        elif self.alertData['alertStatus']:
            # If the website was in alert status and still is, we send a down signal
            return "\n\033[91mWebsite {} is down. Availability={:.2%}, time={}. (Alert {})\033[0m".format(self.URL, availability, str(self.alertData['alertTime']), str(self.alertData['alertNumber']))
        if not(self.alertData['alertStatus']) and availability < 0.8:
            # If the website is now down, we update the alert values and then we send a down signal
            self.alertData['alertNumber'] += 1
            self.alertData['alertStatus'] = True
            self.alertData['alertTime'] = datetime.now()
            return "\n\033[91mWebsite {} is down. Availability={:.2%}, time={}. (Alert {})\033[0m".format(self.URL, availability, str(self.alertData['alertTime']), str(self.alertData['alertNumber']))
        # If there's no problem, we send nothing
        return ""
