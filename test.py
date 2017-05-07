import time
import os
import logging
from influxdb import InfluxDBClient
from multiprocessing import Process
from utils import formatAlert
from flask import Flask
from monitor import Monitor
from retriever import Retriever

# Mock server for testing purposes
# Only has one route which responds to GET requests
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello'

def testServer():
    """Test script for the alerting logic.

    Args:
        retriever (Retriever): Retriever of the test server.
        monitor (Monitor): Monitor of the test server.

    """

    # First, remove flask's logs to avoid cluttering the screen
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    res = []

    influxClient = InfluxDBClient('localhost', 8086, 'root', 'root', 'test')
    influxClient.create_database('test')

    # Create a Monitor and Retriever for the local server
    monitor = Monitor("http://localhost:7000", influxClient)
    retriever = Retriever("http://localhost:7000", influxClient)

    # Clean up the test database
    influxClient.drop_database('test')
    influxClient.create_database('test')

    # Start the server
    server = Process(target=app.run, kwargs={'port':7000})
    server.start()
    print('Starting the server, waiting for first alert check...\n')

    # Take some measurements
    time.sleep(1)
    print('Taking first measurement...\n')
    monitor.get()
    time.sleep(1)
    print('Taking second measurement...\n')
    monitor.get()

    # Do the first alert check
    time.sleep(1)
    alertStatus = retriever.checkAlert()
    if alertStatus['type'] == None:
        # Expect that there are no alerts since the server is up
        # Uptime should be 100%
        print('\n\033[1;92mNo alert (as expected)\033[0m')
        print('Shutting down the server and waiting for alert event...\n')
        res.append(True)

    # Shut down the server
    server.terminate()
    server.join()

    # Take some measurements
    time.sleep(1)
    print('Taking third measurement...\n')
    monitor.get()
    time.sleep(1)
    print('Taking fourth measurement...\n')
    monitor.get()

    time.sleep(1)
    alertStatus = retriever.checkAlert()
    if alertStatus['type'] == 'alert':
        # Expect that there is an alert, since uptime should be 50%
        print(formatAlert(alertStatus))
        print('\033[1;92mAlert (as expected)\033[0m')
        print('Restarting the server and waiting for recovery event...\n')
        res.append(True)

    # Restart the server
    server = Process(target=app.run, kwargs={'port':7000})
    server.start()

    # Take some measurements
    time.sleep(1)
    print('Taking fifth measurement...\n')
    monitor.get()
    time.sleep(1)
    print('Taking sixth measurement...\n')
    monitor.get()
    time.sleep(1)
    print('Taking seventh measurement...\n')
    monitor.get()
    time.sleep(1)
    print('Taking eighth measurement...\n')
    monitor.get()
    time.sleep(1)
    print('Taking ninth measurement...\n')
    monitor.get()
    time.sleep(1)
    print('Taking tenth measurement...\n')
    monitor.get()

    time.sleep(1)
    alertStatus = retriever.checkAlert()
    if alertStatus['type'] == 'recovery':
        # Expect a recovery since uptime should be 80%
        print(formatAlert(alertStatus))
        print('\033[1;92mRecovery (as expected)\033[0m\n')
        res.append(True)

    # We shut down the server for the last time
    server.terminate()
    print('Shutting down the server and waiting for alert event...\n')

    # Take some measurements
    time.sleep(1)
    print('Taking eleventh measurement...\n')
    monitor.get()
    time.sleep(1)
    print('Taking twelvth measurement...\n')
    monitor.get()
    time.sleep(1)

    alertStatus = retriever.checkAlert()
    if alertStatus['type'] == 'alert':
        # Expect an alert since uptime should be 66.67%
        print(formatAlert(alertStatus))
        print('\033[1;92mAlert (as expected)\033[0m')
        res.append(True)

    if len(res) == 4:
        print('\033[1;92mAll checks for the alerting logic are OK\033[0m')
        os._exit(0)
    else:
        print('\033[1;91mAlerting logic checks did not go as expected\033[0m')
        os._exit(1)

