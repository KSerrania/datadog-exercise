# Datadog exercise

Remote uptime and performance monitoring application.

## Installation

To use this application, you need to have python3 and pip3 installed.

To use the test mode, you need to install flask:

`pip3 install flask`

This app uses sqlite as its database.

## Utilisation

The app has three modes : monitoring, notification and test mode.

### Monitoring mode

This is the main mode for the app. In this mode, the websites described in the config.json file are monitored. For details on how to format the configuration file, see the [configuration section](#configjson).

Stats about the monitored website are printed to the console every 10 seconds. Every minute, additional stats about the last hour are also printed.

To start the app in this mode:

`./monitoringApp.py -m`

You can also provide the name of the configuration file (by default, `config.json` is used):

`./monitoringApp.py -m -c <configFilename>`

And you can provide a name for the database file (by default, `monitoring.db`is used):

`./monitoringApp.py -m -db <databaseFileName>`

### Alerts and recoveries notification mode

This mode allows the user to access to the history of alerts and recoveries of the monitored websites. Moreover, if there are also instances of app running in monitoring mode, the history will update periodically to take new notifications into account.

To start the app in this mode:

`./monitoringApp.py -a`

### Alerting logic test mode

This mode executes a test script which verifies that the alerting logic works.
It does so by creating a flask server which answers GET requests and monitoring it during a short while, simulating downtimes and recoveries.

To start the app in this mode:

`./monitoringApp.py -t`

## Structure of the app

### monitoringApp.py

Entry point of the app. Has a method to retrieve stats from the database and return aggregated stats, and a method to check the alert status of the website from the data stored in the database.

### alertWatcher.py

Contains the main class of the notification mode. Retrieves the alert and recovery history and updates it periodically.

### test.py

Contains the test script for the alerting logic.

### utils.py

Contains utility functions to format the printed data.

### dbutils.py

Contains utility functions to communicate with the sqlite database.

### config.json

The main configuration file of the app, which follows the following format:

```json
{
  "websites": [
    {
      "URL": "http://via.ecp.fr",
      "checkInterval": 3.5
    },
    {
      "URL":"http://my.ecp.fr"
    },
  ],
  "defaultCheckInterval": 3
}
```

The `"websites"` key contains an array of objects each representing the individual configuration for a website.

For each website, the `"URL"` field must be filled (a website without a `URL` key will be ignored).

The interval between checks `checkInterval`, in seconds, can be customised for each site. If `checkInterval` isn't given, `defaultCheckInterval` is used for the site.

`defaultCheckInterval` defaults to 2 seconds if not provided.

## Database

sqlite is used for this project, as it is a lightweight database which needs no additional python modules (which is perfect for a small project like this one).
Two tables are used:
* website_monitoring, which stores the data points of the different websites. This table's attributes are:
`(<timestamp (str)>, <host (str)>, <available (int)>, <status (int)>, <responseTime (real)>)`
* website_alerts, which stores the alerts and recoveries notifications. This table's attributes are:
`(<timestamp (str)>, <host (str)>, <type (str)>, <startDate (str)>, <endDate (str)>, <availability (real)>)`

For the test script, a temporary database `test.db` is used to avoid adding unnecessary data to the monitoring database.

## Means of improvement

### About the app:
* Add a silent monitoring mode (monitoring without printing to the console),

* Separate printing and monitoring for the monitoring mode, so that we can print results without doing anything else (the monitoring would be done by another instance in monitoring mode),

* Be able to change / reload the configuration file dynamically,

* Add more interesting monitoring stats (percentiles, duration of the current downtime, time since last failure, ... ?),

* Add a way to purge the database in case of need,

* Verify user input.

### About the architecture:

* Create a Dockerfile for the python part, so that the user doesn't have to install the python packages.
