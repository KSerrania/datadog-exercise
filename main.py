#!/usr/bin/env python3
import os
import threading
from datetime import datetime
from influxdb import InfluxDBClient
from retriever import Retriever
from monitor import Monitor

def printResults(retrievers, printInterval, minutes):
    resultsPrinting = threading.Timer(printInterval, printResults, args=[retrievers, printInterval, minutes])
    resultsPrinting.start()
    totalString = str(datetime.now())
    for website, retriever in retrievers.items():
        availableStats, stats = retriever.getStats(minutes)
        if availableStats:
            alertStatus = retriever.checkAlert()
            totalString += '\n\033[94m---- Stats for website ' + retriever.URL + ' ----\033[0m' + \
                    '\nAverage ping latency over the last {} minutes: {:.2f} ms'.format(minutes, stats['avgRT']) + \
                    '\nMaximum ping latency over the last {} minutes: {:.2f} ms'.format(minutes, stats['maxRT']) + \
                    '\nMinimum ping latency over the last {} minutes: {:.2f} ms'.format(minutes, stats['minRT']) + \
                    '\nSite availibility over the last {} minutes: {:.2%}'.format(minutes, stats['availability']) + \
                    alertStatus + '\n'
        else:
            totalString += '\n\033[93m--- No data available for website ' + retriever.URL + ' ----\033[0m\n'
    print(totalString)
    return 0;

def getResults(monitor, checkInterval):
    periodicCheck = threading.Timer(checkInterval, getResults, args=[monitor, checkInterval])
    periodicCheck.start()
    monitor.get()
    return 0;

def main(*websites, **kwargs):
    influxClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'example')
    influxClient.create_database('example')
    checkInterval = kwargs['checkInterval']
    monitors = {}
    retrievers = {}
    for website in websites:
        monitors[website] = (Monitor(website, influxClient), checkInterval)
        retrievers[website] = Retriever(website, influxClient)

    resultsPrinting10s = threading.Timer(10, printResults, args=[retrievers, 10, 10])
    resultsPrinting10s.start()
    resultsPrinting1m = threading.Timer(60, printResults, args=[retrievers, 60, 60])
    resultsPrinting1m.start()

    for (monitor, checkI) in monitors.values():
        periodicCheck = threading.Timer(checkI, getResults, args=[monitor, checkI])
        periodicCheck.start()

if __name__ == "__main__":
    main('via.ecp.fr', 'my.ecp.fr', 'google.com', 'aefef.co', checkInterval=2)
