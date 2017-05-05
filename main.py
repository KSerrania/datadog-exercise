#!/usr/bin/env python3
import os
import threading
import json
import test
from influxdb import InfluxDBClient
from retriever import Retriever
from monitor import Monitor
from alertWatcher import AlertWatcher
from datetime import datetime
from utils import formatTime, formatStats, formatAlert

class App():
    """Main class of the application. Handles configuration retrieval, checks the app mode
    (main, alert watching and test) and launches the relevant functions.

    Attributes:
        influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.
        monitors (dict of str:(Monitor, int)): Stores the monitor and check interval for each website
        retrievers (dict of str:Retriever): Stores the data retriever for each website

    """
    def __init__(self, database):
        """Initializes the influxDBClient, as well as the monitors ans retrievers dictionaries.
        Also launches the first check which retrieves the whole alert history up to now.

        Args:
            database (str): The database name
        """
        self.influxClient = InfluxDBClient('localhost', 8086, 'root', 'root', database)
        self.influxClient.create_database(database)
        self.monitors = {}
        self.retrievers = {}

    def __loadJSONConfig(self, fileName):
        """Tries to load the configuration file provided in argument.
        The configuration file must have the following format:
        {
            "websites": [
                {
                    "URL": <urlOfWebsite1 (str)>,
                    "checkInterval": <checkIntervalOfWebsite1 (int/float)>
                },
                {
                    "URL": <urlOfWebsite2 (str)>
                }
                ...
            ],
            "defaultCheckInterval": <defaultCheckInterval (intfloat)>
        }
        The check intervals are expressed in seconds.

        Args:
            fileName (str): Path to the configuration file

        Returns:
            A dictionary (str: int/float) containing website / checkInterval key-value pairs
        """
        res = {}

        try:
            file = open(fileName)
            loadedJSON = json.loads(file.read())
            defaultCheckInterval = loadedJSON.get("defaultCheckInterval", 2)
            try:
                websites = loadedJSON["websites"]
            except:
                print("No websites found in the configuration file")
                websites = []
            for website in websites:
                try:
                    res[website['URL']] = website.get("checkInterval", defaultCheckInterval)
                except:
                    print("Error during configuration of website")
            return res
        except FileNotFoundError:
            print("Configuration file not found")
        except Exception as e:
            print("Error while loading file: {}".format(e))

    def __getResults(self, monitor, checkInterval):
        periodicCheck = threading.Timer(checkInterval, self.__getResults, args=[monitor, checkInterval])
        periodicCheck.start()
        monitor.get()
        return 0;

    def __printResults(self, retrievers, printInterval, countdownToNextMinute):
        if countdownToNextMinute == 0:
            resultsPrinting = threading.Timer(printInterval, self.__printResults, args=[retrievers, printInterval, 5])
            printMinuteCheck = True
        else:
            countdownToNextMinute -= 1
            printMinuteCheck = False
            resultsPrinting = threading.Timer(printInterval, self.__printResults, args=[retrievers, printInterval, countdownToNextMinute])
        resultsPrinting.start()

        os.system('clear')

        resString = '\n\033[37;1;4m#### Periodic stat check: ' + formatTime(datetime.now()) + ' ####\033[0m'
        for website, retriever in retrievers.items():
            alertStatus = retriever.checkAlert()
            availableStats2m, stats2m = retriever.getStats(2)
            availableStats10m, stats10m = retriever.getStats(10)
            if printMinuteCheck:
                availableStats1h, stats1h = retriever.getStats(60)
            if availableStats2m:
                resString += '\n\n\033[94;1m---- Stats for website ' + retriever.URL + ' ----\033[0m'
                resString += formatStats(2, stats2m)
                resString += formatStats(10, stats10m)
                if printMinuteCheck and availableStats1h:
                    resString += formatStats(60, stats1h)
                resString += formatAlert(alertStatus)
            else:
                resString += '\n\033[93m--- No data available for website ' + retriever.URL + ' ----\033[0m\n'
        print(resString)
        return 0;

                    
    def run(self, configFile="config.json"):
        websites = self.__loadJSONConfig(configFile)

        for websiteURL, checkInterval in websites.items():
            self.monitors[websiteURL] = Monitor(websiteURL, self.influxClient), checkInterval
            self.retrievers[websiteURL] = Retriever(websiteURL, self.influxClient)

        resultsPrinting = threading.Timer(10, self.__printResults, args=[self.retrievers, 10, 5])
        resultsPrinting.start()

        for (monitor, checkI) in self.monitors.values():
            periodicCheck = threading.Timer(checkI, self.__getResults, args=[monitor, checkI])
            periodicCheck.start()

    def runTest(self):
        monitor = Monitor("http://localhost:7000", self.influxClient)
        retriever = Retriever("http://localhost:7000", self.influxClient)
        self.influxClient.drop_database('test')
        self.influxClient.create_database('test')
        periodicCheck = threading.Timer(2, self.__getResults, args=[monitor, 2])
        periodicCheck.start()

        test.testServer(retriever)

        return 0;

    def runAlert(self):
        alertWatcher = AlertWatcher(self.influxClient)

if __name__ == "__main__":
    app = App('test')
    app.runTest()
