import os
import threading
import json
from influxdb import InfluxDBClient
from retriever import Retriever
from monitor import Monitor
from datetime import datetime
from utils import formatTime, formatStats, formatAlert, formatError

class App():
    """Main class of the application. Handles configuration retrieval, and results printing.

    Attributes:
        influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data,
        monitors (dict of str:(Monitor, int)): Stores the monitor and check interval for each website,
        retrievers (dict of str:Retriever): Stores the data retriever for each website.

    """

    def __init__(self, ):
        """Initializes the influxDBClient, as well as the monitors and retrievers dictionaries.

        """

        self.influxClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'monitoring')
        self.influxClient.create_database('monitoring')
        self.monitors = {}
        self.retrievers = {}

    def __loadJSONConfig(self, fileName):
        """Loads the configuration file provided in argument.
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
            "defaultCheckInterval": <defaultCheckInterval (int/float)>
        }
        The check intervals are expressed in seconds.

        Args:
            fileName (str): Path to the configuration file.

        Returns:
            A dictionary (str: int/float) containing websiteURL: checkInterval key-value pairs.
        """
        res = {}

        try:
            # Load the file and convert it to a dictionary
            file = open(fileName)
            loadedJSON = json.loads(file.read())

            # Get the defaultCheckInterval if there is one (defaults to 2 seconds)
            defaultCheckInterval = loadedJSON.get('defaultCheckInterval', 2)
            try:
                # Try to get the websites config
                websites = loadedJSON['websites']
            except KeyError:
                # If there is no website description in the config, set the websites array to
                # an empty array and print a notification
                websites = {}
                print(formatError('No website descriptors found in the configuration file. Restart the app with a complete configuration file.', 'critical'))
                raise

            for website in websites:
                try:
                    # For each website, add the URL as a key in res, the value associated to it
                    # being the checkInterval (defaults to defaultCheckInterval)
                    res[website['URL']] = website.get("checkInterval", defaultCheckInterval)
                except KeyError:
                    # If the website is misconfigured (no URL), print an error notification
                    print(formatError('Error while reading the configuration file: missing URL for a website.', 'warning'))

            # Return the dictionary of websiteURL: checkInterval
            return res

        except FileNotFoundError:
            # If there's no configuration file
            print(formatError('Configuration file not found. Restart the app with a complete configuration file.', 'critical'))
            raise

        except json.decoder.JSONDecodeError:
            # If there's a syntax error in the configuration file
            print(formatError('\033[1;91mError while decoding configuration file\033[0m', 'critical'))
            raise

    def __getResults(self, monitor, checkInterval):
        """Launches a website check and schedules the next check.
        Args:
            monitor (Monitor): Monitor of the website we want to check
            checkInterval (int/float): Check interval between two checks for this website

        """
        periodicCheck = threading.Timer(checkInterval, self.__getResults, args=[monitor, checkInterval])
        periodicCheck.start()
        monitor.get()
        return;

    def __printResults(self, retrievers, printInterval, countdownToNextMinute):
        """Prints the stats aggregates for defined timeframes for each website.

        Args:
            retrievers (dict of Retriever): Retrievers of the website we want to check
            printInterval (int/float): Interval between two stat prints
            countdownToNextMinute (int): Number of checks to go before the next printing of hourly stats
        """

        if countdownToNextMinute == 0:
            # If it's time to print the hourly stats, set the printHourlyCheck variable to True and schedule the next check
            # with a new countdown of 5 (in order for the newt hourly check to be in one minute)
            resultsPrinting = threading.Timer(printInterval, self.__printResults, args=[retrievers, printInterval, 5])
            printHourlyCheck = True
        else:
            # If not, decrease the countdown by one and schedule the next check
            resultsPrinting = threading.Timer(printInterval, self.__printResults, args=[retrievers, printInterval, countdownToNextMinute - 1])
            printHourlyCheck = False
        resultsPrinting.start()

        # Clear the screen and add the global header to the string to print
        os.system('clear')
        resString = '\n\033[37;1;4m#### Periodic stat check: ' + formatTime(datetime.now()) + ' ####\033[0m'

        for website, retriever in retrievers.items():
            # For each website, get from the retrievers the stats (and whether there are any stats)
            # for the 2 and 10 minutes timeframes. If printHourlyCheck is True, also get the stats
            # for the 60 minutes timeframe.
            alertStatus = retriever.checkAlert()
            availableStats2m, stats2m = retriever.getStats(2)
            availableStats10m, stats10m = retriever.getStats(10)
            if printHourlyCheck:
                availableStats1h, stats1h = retriever.getStats(60)

            # Add the website header to the result string
            resString += '\n\n\033[94;1m---- Stats for website ' + retriever.URL + ' ----\033[0m'

            if availableStats2m:
                # If there are available stats for the past 2 minutes, add them to the result string
                resString += formatStats(2, stats2m)
            if availableStats10m:
                # Same for the last 10 minutes
                resString += formatStats(10, stats10m)
            if printHourlyCheck and availableStats1h:
                # Same for the last hour (if printHourlyCheck is True)
                resString += formatStats(60, stats1h)
            # Finally, add the alert status
            resString += formatAlert(alertStatus)

            if not (availableStats10m and availableStats2m and (not printHourlyCheck or availableStats1h)):
                # If there are no stats available, add a notification to the string"
                resString += '\n\033[93m--- No data available for website ' + retriever.URL + ' ----\033[0m\n'

        # FInally, print the stats for every website
        print(resString)
        return;


    def run(self, configFile="config.json"):
        """Main part of the app.
        Loads the configuration and creates Monitors and Retrievers for each website.
        Prints aggregated data and current errors at constant intervals.

        Args:
            configFile (str): Path to the configuration file
        """

        # Print a waiting message
        print("Initializing monitoring mode... first stats printing expected in 10 seconds.")

        # Load the configuration file
        websites = self.__loadJSONConfig(configFile)

        # Instanciate a Retriever and a Monitor for each website in the configuration file
        for websiteURL, checkInterval in websites.items():
            self.monitors[websiteURL] = Monitor(websiteURL, self.influxClient), checkInterval
            self.retrievers[websiteURL] = Retriever(websiteURL, self.influxClient)

        # Start a thread dedicated to printing results
        resultsPrinting = threading.Timer(10, self.__printResults, args=[self.retrievers, 10, 5])
        resultsPrinting.start()

        for (monitor, checkI) in self.monitors.values():
            # Start a thread dedicated to get stats for each website
            periodicCheck = threading.Timer(checkI, self.__getResults, args=[monitor, checkI])
            periodicCheck.start()

