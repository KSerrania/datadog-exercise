#!/usr/bin/env python3
import os
import threading
import json
from datetime import datetime
from influxdb import InfluxDBClient
from retriever import Retriever
from monitor import Monitor

def formatTime(time):
    return time.strftime("%a, %d/%m/%Y %H:%M:%S")

def printResults(retrievers, printInterval, countdownToNextMinute):
    if countdownToNextMinute == 0:
        resultsPrinting = threading.Timer(printInterval, printResults, args=[retrievers, printInterval, 6])
        printMinuteCheck = True
    else:
        countdownToNextMinute -= 1
        printMinuteCheck = False
        resultsPrinting = threading.Timer(printInterval, printResults, args=[retrievers, printInterval, countdownToNextMinute])
    resultsPrinting.start()
    totalString = '\n\033[37;1;4m#### Periodic stat check: ' + formatTime(datetime.utcnow()) + ' ####\033[0m'
    for website, retriever in retrievers.items():
        availableStats, stats = retriever.getStats(10)
        if printMinuteCheck:
            availableStats1m, stats1m = retriever.getStats(60)
        if availableStats:
            alertStatus = retriever.checkAlert()
            totalString += '\n\n\033[94;1m---- Stats for website ' + retriever.URL + ' ----\033[0m' + \
                    '\n\033[4;93mFor the last 10 minutes:\033[0m' + \
                    '\n\tAverage response time: {:.2f} ms'.format(stats['avgRT']) + \
                    '\n\tMaximum response time: {:.2f} ms'.format(stats['maxRT']) + \
                    '\n\tMinimum response time: {:.2f} ms'.format(stats['minRT']) + \
                    '\n\tResponse counts: {}'.format(stats['statusCodes']) + \
                    '\n\tSite availibility: {:.2%}'.format(stats['availability'])
            if printMinuteCheck and availableStats1m:
                totalString += '\n\033[4;93mFor the last hour:\033[0m' + \
                    '\n\tAverage response time: {:.2f} ms'.format(stats1m['avgRT']) + \
                    '\n\tMaximum response time: {:.2f} ms'.format(stats1m['maxRT']) + \
                    '\n\tMinimum response time: {:.2f} ms'.format(stats1m['minRT']) + \
                    '\n\tResponse counts: {}'.format(stats1m['statusCodes']) + \
                    '\n\tSite availibility: {:.2%}'.format(stats1m['availability'])
            if alertStatus['type'] == 'alert':
                totalString += "\n\033[91mWebsite {} is down. Availability={:.2%}, time={}. (Alert {})\033[0m".format(alertStatus['URL'], alertStatus['availability'], formatTime(alertStatus['alertTime']), alertStatus['alertNumber'])
            elif alertStatus['type'] == 'recovery':
                totalString += "\n\033[92mWebsite {} recovered from alert {}. Availability={:.2%}, time={}\033[0m".format(alertStatus['URL'], alertStatus['alertNumber'], alertStatus['availability'], formatTime(alertStatus['alertTime']))
        else:
            totalString += '\n\033[93m--- No data available for website ' + retriever.URL + ' ----\033[0m\n'
    print(totalString)
    return 0;

def getResults(monitor, checkInterval):
    periodicCheck = threading.Timer(checkInterval, getResults, args=[monitor, checkInterval])
    periodicCheck.start()
    monitor.get()
    return 0;

def main(websites):
    influxClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'example')
    influxClient.create_database('example')
    monitors = {}
    retrievers = {}
    for website, checkInterval in websites.items():
        monitors[website] = (Monitor(website, influxClient), checkInterval)
        retrievers[website] = Retriever(website, influxClient)

    resultsPrinting = threading.Timer(10, printResults, args=[retrievers, 10, 6])
    resultsPrinting.start()

    for (monitor, checkI) in monitors.values():
        periodicCheck = threading.Timer(checkI, getResults, args=[monitor, checkI])
        periodicCheck.start()

def loadJSONConfig(fileName):
    try:
        file = open("config.json")
        return json.loads(file.read())
    except FileNotFoundError:
        print("Configuration file not found")
                    
if __name__ == "__main__":
    websites = loadJSONConfig("./config.json")
    print(websites)
    main(websites)
