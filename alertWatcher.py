#!/usr/bin/env python3
from datetime import datetime
from utils import formatTime, formatAlert, formatError
from dbutils import queryValues, initDatabase
import threading


class AlertWatcher():
    """Class whose goal is to notify about the alerts / recoveries of the monitored websites.
    It checks periodically the monitoring database to see if there are new alerts or recoveries.

    Attributes:
        dbName (str): Name of the database to use.

    """

    def __init__(self, dbName="monitoring.db"):
        """Sets the database name as speficied in the parameters.

        Args:
            dbName (str, optional): Name of the database to use.

        """

        self.dbName = dbName

    def __printData(self, data):
        """Takes the relevant data from the database queries and prints notification lines

        Args:
            data (array): Array of arrays each containing one event data.

        An element of data should always have the following format:
        (<timestamp>, <websiteURL>, <type>, <startDate>, <endDate>, <availability>)
        since this is the format imposed by the sql query we made.
        If it doesn't, that means that the database was modified or that
        the query (or its result) was tampered with.

        """

        for elt in data:
            # For each data point, print the correspnding alert or recovery notification
            try:
                lineData = {
                    "URL": elt[1],
                    "type": elt[2],
                    "startDate": elt[3],
                    "endDate": elt[4],
                    "availability": elt[5]
                }
                print(formatAlert(lineData))
            except:
                print(formatError('Error while reading data', 'critical'))
                raise

    def __check(self, startDate=None):
        """Checks if there are any new notifications to take into account and prints them.

        Args:
            startDate (str, optional): Limits the search to notifications after this date.

        """

        if startDate is not None:
            # If a startDate was given (typically, after the first check), only query about notifications after this date.
            queryData = {
                "startDate": startDate
            }
        else:
            # Query the database about all the notifications
            queryData = {}
        data = queryValues(self.dbName, 'website_alerts', queryData)

        if len(data) > 0:
            # If there is new data available, print it
            self.__printData(data)

            # The query returns events in ascending time order.
            # Take the last timestamp as the starting point for next check
            currentDate = data[-1][0]
        else:
            # There were no new events, keep the previous starting point as the next start date
            currentDate = startDate

        # Schedule the next check
        newCheck = threading.Timer(10, self.__check, args=[currentDate])
        newCheck.start()
        return 0;

    def run(self):
        """Launches the first check which retrieves all notification history.

        """

        initDatabase(self.dbName)
        self.__check()

