#!/usr/bin/env python3
import time
import os
import logging
from multiprocessing import Process
from utils import formatAlert
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello'

def testServer(retriever):
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    res = []
    server = Process(target=app.run, kwargs={'port':7000})
    server.start()
    print('Starting the server, waiting for first alert check...\n')
        
    time.sleep(5)
    alertStatus = retriever.checkAlert()
    if alertStatus['type'] == None:
        print('\n\033[1;92mNo alert (as expected)\033[0m')
        print('Shutting down the server and waiting for alert event...\n')
        res.append(True)

    server.terminate()
    server.join()

    time.sleep(5)
    alertStatus = retriever.checkAlert()
    if alertStatus['type'] == 'alert':
        print(formatAlert(alertStatus))
        print('\033[1;92mAlert (as expected)\033[0m')                
        print('Restarting the server and waiting for recovery event...\n')
        res.append(True)

    server = Process(target=app.run, kwargs={'port':7000})
    server.start()

    for i in range(8):
        time.sleep(5)
        alertStatus = retriever.checkAlert()
        if alertStatus['type'] == 'recovery':
            print(formatAlert(alertStatus))                
            print('\033[1;92mRecovery (as expected)\033[0m\n')
            res.append(True)
            break
        else:
            print(formatAlert(alertStatus))
            print('Website uptime still not over threshold\n')
    server.terminate()
    print('Shutting down the server and waiting for alert event...\n')
    
    time.sleep(10)
    alertStatus = retriever.checkAlert()
    if alertStatus['type'] == 'alert':
        print(formatAlert(alertStatus))
        print('\033[1;92mAlert (as expected)\033[0m')                
        res.append(True)

    if len(res) == 4:
        print('\033[1;92mAll checks for the alerting logic are OK\033[0m')
        os._exit(0)
    else:
        print('\033[1;91mSome alerting logic checks did not go as expected\033[0m')
        os._exit(1)

