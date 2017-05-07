from collections import Counter
from datetime import datetime
from utils import formatTime, getQueryValues

class Retriever():
    """Class whose goal is to get a website's monitoring data and compute interesting metrics about it.
    It also has a method to track and warn about availability alerts.

    Attributes:
        URL (str): URL of the monitored website,
        influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data,

    """

    def __init__(self, URL, influxClient):
        """Sets the URL and influxDBClient as speficied in the parameters.

        Args:
            URL (str): URL of the monitored website,
            influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.

        """
        self.URL = URL
        self.influxClient = influxClient

    def getStats(self, minutes):
        """Retrieves data about the monitored website from the InfluxDB database.
        The data retrieved is only the data recorded during the last {minutes} minutes;

        Args:
            minutes (int): Number of minutes in the past over which data is retrieved.

        Returns:
            A tuple composed of:
                - a boolean (False if the is no data about the website for the specified timespan, True otherwise),
                - a dictionary containing interesting stats about the website for the specified timeframe:
                    availability (float): Availability of the website,
                    statusCodes (collections.Counter): Counts of the different response codes from requests on the website,
                    avgRT (float): Average response time,
                    minRT (float): Minimum response time,
                    maxRT (float): Maximum response time.

        """

        # First, query the database
        query = "SELECT available, status, responseTime FROM website_availability WHERE time > now() - {}m AND host = '{}'".format(minutes, self.URL)
        data = getQueryValues(self.influxClient, query)

        if len(data) > 0:
            # If there is available data
            # Create a counter of number of times the site was available or not
            availables = Counter([elt[1] for elt in data if elt[1] is not None])

            # Create an array containing all the (not None) response times
            responseTimes = [elt[3] for elt in data if elt[3] is not None]

            # Create a counter of status codes
            statusCodes = Counter([elt[2] for elt in data])
        else:
            # If there is no data available, return that there is no data available
            return False, {}

        # Compute some interesting statistics
        nRT = len(responseTimes)
        minRT = min(responseTimes, default=float('inf'))
        maxRT = max(responseTimes, default=float('inf'))
        try:
            avgRT = sum(responseTimes) / nRT
        except:
            avgRT = float('inf')

        # Define the availability
        n = sum(availables.values())
        availability = availables[True] / n

        # And return these stats in a dictionary
        return True, {
                'availability': availability,
                'statusCodes': statusCodes,
                'avgRT': avgRT,
                'minRT': minRT,
                'maxRT': maxRT,
                }

    def checkAlert(self):
        """Checks if an availability alert (or recovery) message should be sent, and also stores the notification data in
        the influxDB database.
        The check timeframe is 2 minutes.

        Returns:
            A dictionary composed of:
                - type (str): Type of notification (or None if there is no notification; in that case, the following
                  fields do not exist),
                - URL (str): Website URL,
                - availability (float): Availability of the website at the time of notification,
                - startDate (str): Date of alert,
                - endDate (str, optional): Date of recovery (only in case of a recovery),
        """

        # First retrieve the website's data on the last 2 minutes
        query = "SELECT available FROM website_availability WHERE time > now() - 2m AND host = '{}'".format(self.URL)
        data = getQueryValues(self.influxClient, query)
        availables = Counter([elt[1] for elt in data])
        n = sum(availables.values())

        # Compute the site's availability
        availability = availables[True] / n
        currentDate = datetime.utcnow()

        # Then, get the last notification about the website in order to know its current status
        query = "SELECT type, startDate FROM website_alerts WHERE host = '{}' ORDER BY time DESC LIMIT 1".format(self.URL)
        data = getQueryValues(self.influxClient, query)


        if len(data) == 0:
            # There is no notification about the website in the database
            isOnAlert = False
        else:
            # There is data about the last notification in data, in the following format:
            # data = [[ <timestamp>, <type>, <availability> ]]
            if data[0][1] == 'alert':
                isOnAlert = True
                startDate = data[0][2]
            else:
                isOnAlert = False

        if isOnAlert and availability >= 0.8:
            # If the website was in alert status but has recovered, we send a recovery signal and store the recovery
            # in the database
            data = [
                {
                    'measurement': 'website_alerts',
                    'tags': {
                        'host': self.URL
                    },
                    'time': currentDate.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'fields': {
                        'type': 'recovery',
                        'startDate': startDate,
                        'endDate': formatTime(currentDate),
                        'availability': availability,
                    }
                }
            ]
            self.influxClient.write_points(data)
            return {
                'type': 'recovery',
                'URL': self.URL,
                'availability': availability,
                'startDate': startDate,
                'endDate': formatTime(currentDate),
            }

        elif isOnAlert:
            # If the website was in alert status and still is, send a downtime signal
            return {
                'type': 'alert',
                'URL': self.URL,
                'availability': availability,
                'startDate': startDate,
            }
        if not(isOnAlert) and availability < 0.8:
            # If the website is now down, update the alert values and then send a downtime signal
            # Also write the alert notification in the database
            data = [
                {
                    'measurement': 'website_alerts',
                    'tags': {
                        'host': self.URL
                    },
                    'time': currentDate.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'fields': {
                        'type': 'alert',
                        'startDate': formatTime(currentDate),
                        'availability': availability,
                    }
                }
            ]
            self.influxClient.write_points(data)

            return {
                'type': 'alert',
                'URL': self.URL,
                'availability': availability,
                'startDate': formatTime(currentDate),
            }

        # If there's no problem, only send that type is None
        return { 'type': None }
