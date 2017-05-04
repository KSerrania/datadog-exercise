#!/usr/bin/env python3 
import argparse
from main import App

parser = argparse.ArgumentParser(prog='main', usage='%(prog)s [options]')

parser.add_argument('--monitor', action='store_true')
parser.add_argument('--alert', action='store_true')
parser.add_argument('--test', action='store_true')
parser.add_argument('--configFile', action='store')

args = vars(parser.parse_args())

if args['monitor']:
    app = App('monitoring')
    if args['configFile'] is not None:
        app.run(args['configFile'])
    else:
        app.run()
elif args['alert']:
    app = App('monitoring')
    app.runAlert()
elif args['test']:
    app = App('test')
    app.runTest()
else:
    print('Missing argument')
