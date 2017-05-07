#!/usr/bin/env python3
from datetime import datetime
from influxdb import InfluxDBClient
from utils import formatTime, formatAlert, getQueryValues, formatError
import threading


class AlertWatcher():
    """Class whose goal is to notify about the alerts / recoveries of the monitored websites.
    It checks periodically the monitoring database to see if there are new alerts or recoveries.

    Attributes:
        influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.

    """

    def __init__(self):
        """Sets the influxDBClient as speficied in the parameters.

        """

        # Set the influxClient
        self.influxClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'monitoring')
        self.influxClient.create_database('monitoring')

    def __printData(self, data):
        """Takes the relevant data from the database queries and prints notification lines

        Args:
            data (array): Array of arrays each containing one event data.

        An element of data should always have the following format:
        [<timestamp>, <websiteURL>, <type>, <startDate>, <endDate>, <availability>]
        since this is the format imposed by the influxDB query we made.
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
        """Checks if there are any new notifications to take into account and prints them

        Args:
            startDate (str, optional): Limits the search to notifications after this date.

        """

        if startDate is not None:
            # If a startDate was given (typically, after the first check), only query about notifications after this date.
            # The data needs to be in the following format, as absolute dates in InfluxDB queries must follow RFC3339_like_date_time
            # or RFC3339_date_time
            query = "SELECT host, type, startDate, endDate, availability FROM website_alerts WHERE time > '{}'".format(startDate)
        else:
            # Query the database about all the notifications
            query = "SELECT host, type, startDate, endDate, availability FROM website_alerts"
        data = getQueryValues(self.influxClient, query)

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
        self.__check()

