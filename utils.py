from datetime import datetime

def formatTime(time):
    """Takes a string representation of a date compatible with the database and returns a string representing it in a better format.

    Args:
        time (str): String representation of a date in the format "%d/%m/%Y %H:%M:%S"

    Returns:
        A pretty string representation of the date

    """

    return datetime.strptime(time, "%d/%m/%Y %H:%M:%S").strftime("%a, %d/%m/%Y %H:%M:%S")

def printCounter(counter):
    """Takes a collections.Counter object and returns a string representing it in a user-friendly format

    Args:
        time (collections.Counter): Counter object to format

    Returns:
        A pretty string representation of the collections.Counter object
    """

    formattedCounts = []
    for value, count in counter.most_common():
        # For each element in the counter, print it in a diffrerent color depending on the response code
        formattedStat = ''

        if value is not None and value < 400:
            formattedStat += '\033[92m'
        else:
            formattedStat+= '\033[91m'

        formattedStat += '{}: {}\033[0m'.format(value, count)
        formattedCounts.append(formattedStat)

    # Finally join each element of the counter to have only one resulting string
    return '({})'.format("; ".join(formattedCounts))

def formatStats(minutes, stats):
    """Takes stats and returns a string representing them in a user-friendly format.

    Args:
        minutes (int): Timeframe of the stats aggregation,
        stats (dict): Stats to be printed:
            availability (float): Availability of the website,
            statusCodes (collections.Counter): Counts of the different response codes from requests on the website,
            avgRT (float): Average response time,
            minRT (float): Minimum response time,
            maxRT (float): Maximum response time.

    Returns:
        A pretty string representation of the stats.
    """

    return '\n\033[4;93mFor the past {} minutes:\033[0m'.format(minutes) + \
    '\n\tMin/Avg/Max response time: {:.2f}/{:.2f}/{:.2f} ms'.format(stats['minRT'], stats['avgRT'], stats['maxRT']) + \
    '\n\tResponse counts: {}'.format(printCounter(stats['statusCodes'])) + \
    formatUptime(stats['availability'])

def formatUptime(uptime):
    """Takes uptime returns a string representing it in a user-friendly format.

    Args:
        uptime (float): Uptime stat.

    Returns:
        A pretty string representation of the collections.Counter object.
    """

    if uptime >= 0.9:
        return '\n\t\033[1mUptime: \033[92m{:.2%}\033[0m'.format(uptime)
    elif uptime >= 0.8:
        return '\n\t\033[1mUptime: \033[93m{:.2%}\033[0m'.format(uptime)
    else:
        return '\n\t\033[1mUptime: \033[91m{:.2%}\033[0m'.format(uptime)

def formatAlert(alertData):
    """Takes notification data and returns a string representing it in a user-friendly format.

    Args:
        alertData (dict): Data about the notification:
            type (str): Type of notification (or None if there is no notification; in that case, the following
            fields do not exist),
            URL (str): Website URL,
            availability (float): Availability of the website at the time of notification,
            startDate (datetime.datetime): Date of alert,
            endDate (datetime.datetime, optional): Date of recovery (only in case of a recovery),

    Returns:
        A pretty string representation of the collections.Counter object.
    """

    try:
        if alertData['type'] == 'alert':
            return "\n\033[91mWebsite {} is down. Uptime: {:.2%}\nStart date: {}. \033[0m".format(alertData['URL'], alertData['availability'], alertData['startDate'])
        elif alertData['type'] == 'recovery':
            return "\n\033[92mWebsite {} recovered from alert. Uptime: {:.2%}\nStart date: {},\nEnd date: {}\033[0m".format(alertData['URL'], alertData['availability'], alertData['startDate'], alertData['endDate'])
        else:
            return ""
    except KeyError:
        print(formatError('Wrong alertData structure given to formatAlert', 'critical'))
        raise

def getQueryValues(influxClient, query):
    """Takes an influxDB query and returns the corresponding useful data
    Args:
        influxClient (InfluxDBClient): Client for the InfluxDB to query,
        query (str): Query to process.

    Returns:
        An array of arrays containing the queried data for each timestamp
    """

    # Query the database and retrieve all the data in a dictionary format
    try:
        data = influxClient.query(query).raw
    except:
        print(formatError("Error while querying influxDB", 'warning'))
        data = {}

    # The raw data from the query is a dictionary object.
    # The interesting data is associated to the series key
    if 'series' in data.keys():
        # If there is available data
        # data['series'] is an array whose only relevant element is the first
        # This element (data['series'][0]) contains another dictionary
        # In the 'values' key of this dictionary, there is an array of arrays whose first element is the time
        # and whose following elements are the elements we requested, in the order they were requested
        #
        # Example : [ [<timestamp>, <statusCode>], [<timestamp>, <statusCode>], ...] for the query:
        # SELECT statusCode FROM website_availability
        return data['series'][0]['values']
    else:
        return []

def formatError(error, level):
    """Takes an error message and colors it to correspond to its level.

    Args:
        error (str): Error string to be printed,
        level (str): Level of the error.

    Returns:
        A pretty string representation of the error.
    """

    if level == 'critical':
        return '\033[92;1m{}\033[0m'.format(error)
    elif level == 'warning':
        return '\033[91;1m{}\033[0m'.format(error)
    else:
        return error
