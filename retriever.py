from collections import Counter
from datetime import datetime
from utils import formatTime
from dbutils import queryValues, queryLastValue, insertValue

class Retriever():
    """Class whose goal is to get a website's monitoring data and compute interesting metrics about it.
    It also has a method to track and warn about availability alerts.

    Attributes:
        URL (str): URL of the monitored website,
        dbName (str): Name of the database to use,
        isOnAlert (bool): Indicates alert status locally.
    """

    def __init__(self, URL, dbName):
        """Sets the URL and database name as speficied in the parameters.

        Args:
            URL (str): URL of the monitored website,
            dbName (str): Name of the database to use.

        """

        self.URL = URL
        self.isOnAlert = False
        self.dbName = dbName

    def getStats(self, minutes):
        """Retrieves data about the monitored website from the database.
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
        queryData = {
            "host": self.URL,
            "minutes": minutes
        }
        data = queryValues(self.dbName, 'website_monitoring', queryData)

        if len(data) > 0:
            # If there is available data
            # Create a counter of number of times the site was available or not
            availables = Counter([elt[1] for elt in data if elt[1] is not None])

            # Create a counter of status codes
            statusCodes = Counter([elt[2] for elt in data])

            # Create an array containing all the (not None) response times
            responseTimes = [elt[3] for elt in data if elt[3] is not None]
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

        # Compute the availability
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
        the database.
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

        # First, get the last notification about the website in order to know its current status
        queryData = {
            'host': self.URL,
        }
        data = queryLastValue(self.dbName, 'website_alerts', queryData)

        if data is None:
            # There are no notifications about the website in the database
            isOnAlert = False
        else:
            # There is data about the last notification in data, in the following format:
            # data = [[ <timestamp>, <type>, <availability> ]]
            if data[2] == 'alert':
                isOnAlert = True
                startDate = data[3]
            else:
                isOnAlert = False
                startDate = data[3]
                endDate = data[4]

        # Then, retrieve the website's data on the last 2 minutes
        queryData = {
            "host": self.URL,
            "minutes": 2
        }
        data = queryValues(self.dbName, 'website_monitoring', queryData)

        availables = Counter([elt[1] for elt in data])
        n = sum(availables.values())
        if n == 0:
            # If there is no data about the website in the past 2 minutes, it is not possible to
            # assert the site's status, we return that there is no new notification
            return { 'type': None }

        # Compute the site's availability
        availability = availables[True] / n
        currentDate = datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')


        if isOnAlert and self.isOnAlert and availability >= 0.8:
            # If the website was in alert status locally and in the database but has recovered,
            # we send a recovery signal and store the recovery in the database
            # Change the local alert state to False
            self.isOnAlert = False

            # Add recovery data to the database
            queryData = {
                'host': self.URL,
                'timestamp': currentDate,
                'type': 'recovery',
                'startDate': startDate,
                'endDate': currentDate,
                'availability': availability,
            }
            insertValue(self.dbName, 'website_alerts', queryData)

            # Return data about the recovery
            return {
                'type': 'recovery',
                'URL': self.URL,
                'availability': availability,
                'startDate': startDate,
                'endDate': currentDate
            }

        if not(isOnAlert) and self.isOnAlert and availability >= 0.8:
            # If the website was in alert status locally but has recovered (the recovery signal has already been
            # sent by another retriever), we send a recovery signal without storing it to the database
            # Change the local alert state to False
            self.isOnAlert = False

            # Return data about the recovery
            return {
                'type': 'recovery',
                'URL': self.URL,
                'availability': availability,
                'startDate': startDate,
                'endDate': endDate
            }

        if isOnAlert:
            # If the website was in alert status and still is, send a downtime signal
            # Change the local alert state to True
            self.isOnAlert = True

            # Return data about the alert
            return {
                'type': 'alert',
                'URL': self.URL,
                'availability': availability,
                'startDate': startDate
            }

        if not(isOnAlert) and availability < 0.8:
            # If the website is now down, update the alert values and then send a downtime signal
            # Also write the alert notification in the database
            # Change the local alert state to True
            self.isOnAlert = True

            # Add data about the alert in the database
            queryData = {
                'host': self.URL,
                'timestamp': currentDate,
                'type': 'alert',
                'startDate': currentDate,
                'endDate': None,
                'availability': availability,
            }
            insertValue(self.dbName, 'website_alerts', queryData)

            return {
                'type': 'alert',
                'URL': self.URL,
                'availability': availability,
                'startDate': currentDate,
            }

        # If there's no problem, only send that type is None
        return { 'type': None }
