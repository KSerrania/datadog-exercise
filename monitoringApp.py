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
parser.add_argument

# Parse the args
args = vars(parser.parse_args())

if args['monitor']:
    # If the app is run in monitoring mode, initialize it
    app = App()
    if args['config'] is not None:
        # If a config file is provided, use it
        app.run(args['config'])
    else:
        # If not, use the default config file (config.json)
        app.run()
elif args['alert']:
    # If the app is run in  mode, initialize it
    app = AlertWatcher()
    app.run()
elif args['test']:
    testServer()
else:
    print('Missing argument')
