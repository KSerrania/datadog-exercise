#!/usr/bin/env python3
import argparse
from app import App
from alertWatcher import AlertWatcher
from test import testServer

# Add the different possible args for the app
parser = argparse.ArgumentParser(prog='main', usage='%(prog)s [options]')
parser.add_argument('--monitor', '-m', action='store_true', help='start the app in monitoring mode')
parser.add_argument('--alert', '-a', action='store_true', help='start the app in alert / recovery notification mode')
parser.add_argument('--test', '-t', action='store_true', help='start the app in test mode')
parser.add_argument('--config', '-c', action='store', help='give the configuration filename (with -m only)')
parser.add_argument('--database', '-db', action='store', help='give the database filename (with -m only)')
parser.add_argument

# Parse the args
args = vars(parser.parse_args())

if args['monitor']:
    # If the app is run in monitoring mode, initialize it
    app = App()

    # Run the app with the corresponding config
    if args['database'] and args['config']:
        app.run(dbName=args['database'], configFile=args['config'])
    elif args['database']:
        app.run(dbName=args['database'])
    elif args['config']:
        app.run(dbName=args['config'])
    else:
        app.run()

elif args['alert']:
    # If the app is run in alert mode, initialize it
    app = AlertWatcher()
    app.run()

elif args['test']:
    # If the app is run in test mode, launch the test script
    testServer()

else:
    print('Missing argument: use -m, -a or -t')
