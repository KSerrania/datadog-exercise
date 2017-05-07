from datetime import datetime

def formatTime(time):
    """Takes a datetime.datetime object and returns a string representing it in a user-friendly format

    Args:
        time (datetime.datetime): Datetime object to format

    Returns:
        A pretty string representation of the datetime.datetime object
    """

    return time.strftime("%a, %d/%m/%Y %H:%M:%S")

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
    if alertData['type'] == 'alert':
        return "\n\033[91mWebsite {} is down. Uptime: {:.2%}, Start date: {}. (Alert {})\033[0m".format(alertData['URL'], alertData['availability'], formatTime(alertData['startDate']), alertData['alertNumber'])
    elif alertData['type'] == 'recovery':
        return "\n\033[92mWebsite {} recovered from alert {}. Uptime: {:.2%}, Start date: {}, End date: {}\033[0m".format(alertData['URL'], alertData['alertNumber'], alertData['availability'], formatTime(alertData['startDate']), formatTime(alertData['endDate']))
    else:
        return ""
