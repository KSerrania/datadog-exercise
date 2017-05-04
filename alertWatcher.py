#!/usr/bin/env python3
from datetime import datetime
from influxdb import InfluxDBClient
from utils import formatTime
import threading


class AlertWatcher():
    """Class whose goal is to notify about the alerts / recoveries of the monitored websites.
    It checks periodically the monitoring database to see if there are new alerts or recoveries.

    Attributes:
        influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.

    """
    def __init__(self):
        """Sets the influxDBClient as speficied in the parameters.
        Also launches the first check which retrieves the whole alert history up to now.

        Args:
            influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.

        """
        influxClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'monitoring')
        influxClient.create_database('monitoring')

        # We set the influxClient and launch the initial data check
        self.influxClient = influxClient
        self.__check()

    def __printLine(self, lineData):
        """Prints a line notifying an alert or a recovery

        Args:
            lineData (dict): Data about the alert or recovery.
                type (string): Type of notification.
                URL (string): URL of the website the notification is about. 
                availability (float): Website availability at the time of the notification.
                time (datetime.datetime): Time of the notification.
        """

        if lineData['type'] == 'alert':
            # If the notification is an alert
            print("\n\033[91mWebsite {} is down. Availability={:.2%}, time={}.".format(lineData['URL'], lineData['availability'], formatTime(lineData['time'])))
        elif lineData['type'] == 'recovery':
            # If the notification is a recovery
            print("\n\033[92mWebsite {} recovered from alert. Availability={:.2%}, time={}\033[0m".format(lineData['URL'], lineData['availability'], formatTime(lineData['time'])))
        else:
            # The notification is of an unknown type
            pass
    
    def __printData(self, data):
        """Takes the relevant data from the database queries and prints notification lines

        Args:
            data (array): Array of arrays each containing one event data.
        
        An element of data should always have the following format:
        [time, websiteURL, type, availability] 
        since this is the format imposed by the influxDB query we made.
        If it doesn't, that means that the database was modified or that
        the query (or its result) was tampered with.
        """

        #TODO: Check types
        for elt in data:
            try:
                lineData = {
                    "time": datetime.strptime(elt[0],"%Y-%m-%dT%H:%M:%SZ"), 
                    "URL": elt[1],
                    "type": elt[2],
                    "availability": elt[3]
                }
                self.__printLine(lineData)
            except:
                pass

    def __check(self, startDate=None):
        """Checks if there are any new notifications to take into account and prints them

        Args:
            startDate (datetime.datetime, optional): Limits the search to notifications after this date.

        """

        if startDate is not None:
            # If a startDate was given (typically, after the first check), we only query about notifications after this date.
            # The data needs to be in the following format, as absolute dates in InfluxDB queries must follow RFC3339_like_date_time 
            # or RFC3339_date_time
            data = self.influxClient.query("SELECT host, type, availability FROM website_alerts WHERE time > '{}'".format(startDate)).raw            
        else:
            # We query the database about all the notifications
            data = self.influxClient.query("SELECT host, type, availability FROM website_alerts").raw
        
        if 'series' in data.keys():
            # If there is new data available, we print it
            self.__printData(data['series'][0]['values'])

            # The query returns events in ascending time order. 
            # We take the last timestamp as the next starting point for our check
            currentDate = data['series'][0]['values'][-1][0]
        else:
            # There were no new events, we can keep the previous starting point as the next start date
            currentDate = startDate

        # We schedule the next check
        newCheck = threading.Timer(10, self.__check, args=[currentDate])
        newCheck.start()
        return 0;

if __name__ == "__main__":
    alertWatcher = AlertWatcher()


