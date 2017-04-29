import os
import threading
from datetime import datetime
from influxdb import InfluxDBClient
from retriever import Retriever
from monitor import Monitor

def printResults(retriever, printInterval, minutes):
    resultsPrinting = threading.Timer(printInterval, printResults, args=[retriever, 10, 10]) 
    resultsPrinting.start()
    stats = retriever.getStats(minutes)   
    alertStatus = retriever.checkAlert()
    
    print('\n\033[94m--- Stats for website ' + retriever.URL + ' ----\033[0m' + \
            '\nAverage ping latency over the last {} minutes: {:.2f} ms'.format(minutes, stats['avgLatency']) + \
            '\nMaximum ping latency over the last {} minutes: {:.2f} ms'.format(minutes, stats['maxLatency']) + \
            '\nMinimum ping latency over the last {} minutes: {:.2f} ms'.format(minutes, stats['minLatency']) + \
            '\nPing response over the last {} minutes: {:.2%}'.format(minutes, stats['pingResponse']) + \
            '\nSite availibility over the last {} minutes: {:.2%}'.format(minutes, stats['availability']) + \
            alertStatus)
    return 0;

def getResults(monitor, checkInterval):
    periodicCheck = threading.Timer(checkInterval, getResults, args=[monitor, checkInterval])
    periodicCheck.start()
    monitor.get()
    return 0;

def monitorWebsite(website, influxClient, checkInterval):
    monitor = Monitor(website, influxClient)
    retriever = Retriever(website, influxClient)
    resultsPrinting10s = threading.Timer(10, printResults, args=[retriever, 10, 10])
    resultsPrinting10s.start()
    resultsPrinting1m = threading.Timer(60, printResults, args=[retriever, 60, 60])
    resultsPrinting1m.start()
    periodicCheck = threading.Timer(checkInterval, getResults, args=[monitor, checkInterval])
    periodicCheck.start()

def main(*websites, **kwargs):
    influxClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'example')
    influxClient.create_database('example')
    threads = {}
    checkInterval = kwargs['checkInterval']
    for website in websites:
        threads[website] = threading.Thread(target=monitorWebsite, name=website,args=[website, influxClient, checkInterval])
        threads[website].daemon = True
        threads[website].start()
