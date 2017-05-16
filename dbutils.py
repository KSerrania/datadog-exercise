import sqlite3

"""Module dedicated to the interaction with a sqlite database.

    The functions below could also be grouped into a single DatabaseConnection class,
    but as sqlite connections are only usable by a single thread, we would have
    to create an instance of DatabaseConnection for each thread.

"""

def initConnection(dbName):
    """Creates a connection and cursor object for the the given database.

    Args:
        dbName (str): Name of the database to use.

    Returns:
        A tuple containing:
            - a sqlite3.connection object containing for the current database connection,
            - a sqlite3.connection.cursor object for data querying and manipulation in the database.

    """

    connection = sqlite3.connect(dbName)
    cursor = connection.cursor()
    return connection, cursor

def initDatabase(dbName):
    """Creates the database tables website_alerts and website_monitoring (if they do not exist).

    Args:
        dbName (str): Name of the database to use.

    """

    # Initialize the database connection
    connection, cursor = initConnection(dbName)

    # Create the website_alerts table
    cursor.execute("CREATE TABLE IF NOT EXISTS website_alerts \
         (host text, timestamp text, type text, startDate text, endDate text, availability real)")

    # Create the website_monitoring table
    cursor.execute("CREATE TABLE IF NOT EXISTS website_monitoring \
         (host text, timestamp text, available integer, status integer, responseTime real)")

    # Save the changes to the database
    connection.commit()
    connection.close()

def dropTables(dbName):
    """Drop the database tables website_alerts and website_monitoring.

    Args:
        dbName (str): Name of the database to use.

    """

    # Initialize the database connection
    connection, cursor = initConnection(dbName)

    # Drop the website_alerts table
    cursor.execute("DROP TABLE IF EXISTS website_alerts")

    # Drop the website_monitoring table
    cursor.execute("DROP TABLE IF EXISTS website_monitoring")

    # Save the changes to the database
    connection.commit()
    connection.close()

def insertValue(dbName, table, data):
    """Insert given value set into a given table.

    Args:
        dbName (str): Name of the database to use,
        table (str): Name of the table to modify,
        data (dict): Dictionary containing the data to insert. The data itself depends on what table is modified:
            - if table == "website_monitoring":
                timestamp (str): String representing the date at which the measurement was taken,
                host (str): Name of the monitored website,
                available (bool): Stores whether the site is available or not,
                status (int): Response status code of the site,
                responseTime (float): Time the site took to answer a request.
            - if table == "website_alerts":
                timestamp (str): String representing the date at which the measurement was taken,
                host (str): Name of the monitored website,
                type (str): Type of notification,
                startDate (str): String representing the date of start of the alert,
                endDate (str, optional): String representing the date of end of the alert,
                availability (float): Availability of the website.

    """

    # Initialize the database connection
    connection, cursor = initConnection(dbName)

    if table == 'website_alerts':
        # If the insertion concerns the website_alerts table
        # Get the relevant fields in order
        fields = (data['host'], data['timestamp'], data['type'], data['startDate'], data['endDate'], data['availability'])

        # Insert the data in the database
        cursor.execute("INSERT INTO website_alerts VALUES (?, ?, ?, ?, ?, ?)", fields)

        # Save the changes to the database
        connection.commit()

    if table == 'website_monitoring':
        # If the insertion concerns the website_monitoring table
        # Get the relevant fields in order
        fields = (data['host'], data['timestamp'], data['available'], data['status'], data['responseTime'])

        # Insert the data in the database
        cursor.execute("INSERT INTO website_monitoring VALUES (?, ?, ?, ?, ?)", fields)

        # Save the changes to the database
        connection.commit()
    connection.close()

def queryLastValue(dbName, table, queryData):
    """Get the most recent value in a table for a host.

    Args:
        dbName (str): Name of the database to use,
        table (str): Name of the table to query,
        data (dict): Dictionary containing the parameters of the query:
            host (str): Name of the website the query is about.

    Returns:
        A tuple containing the retrieved data (which may be empty). Its content depends on the queried table:
            - if table == "website_alerts":
                (<timestamp (str)>, <host (str)>, <type (str)>, <startDate (str)>, <endDate (str)>, <availability (float)>)
            - if table == "website_monitoring":
                (<timestamp (str)>, <available (bool)>, <status (int)>, <responseTime (float)>)

    """

    # Initialize the database connection
    connection, cursor = initConnection(dbName)

    if table == 'website_alerts':
        # If the query concerns the website_alerts table
        # Get the host
        fields = (queryData['host'],)

        # Query the database
        cursor.execute('SELECT timestamp, host, type, startDate, endDate, availability FROM website_alerts \
                WHERE host = ? \
                ORDER BY timestamp DESC LIMIT 1', fields)

        # Returns the gathered data (which is only one row)
        result = cursor.fetchone()
        connection.close()
        return result

    if table == 'website_monitoring':
        # If the query concerns the website_monitoring table
        # Get the host
        fields = (queryData['host'],)

        # Query the database
        cursor.execute("SELECT timestamp, available, status, responseTime FROM website_monitoring \
                WHERE host = ? \
                ORDER BY timestamp DESC LIMIT 1", fields)

        # Returns the gathered data (which is only one row)
        result = cursor.fetchone()
        connection.close()
        return result

def queryValues(dbName, table, queryData):
    """Get the values in a table.
    The query can be global or for a host, optionally only for the past few minutes or since a given date.

    Args:
        dbName (str): Name of the database to use,
        table (str): Name of the table to query,
        data (dict): Dictionary containing the parameters of the query:
            host (str, optional): Name of the website the query is about,
            startDate (str, optional): Restricts the query to results which timestamp are after this date,
            minutes (int, optional): Restricts the query to results which timestamp is less than this number of minutes old.

    Returns:
        An array of tuples containing the retrieved data (which may be empty). Its content depends on the queried table:
            - if table == "website_alerts":
                [(<timestamp (str)>, <host (str)>, <type (str)>, <startDate (str)>, <endDate (str)>, <availability (float)>)]
            - if table == "website_monitoring":
                [(<timestamp (str)>, <available (bool)>, <status (int)>, <responseTime (float)>)]

    """

    # Initialize the database connection
    connection, cursor = initConnection(dbName)

    if table == 'website_alerts':
        # If the query concerns the website_alerts table

        if 'startDate' in queryData.keys():
            # If a startDate was defined (by an alertChecker, for example), get it
            fields = (queryData['startDate'],)

            # Query the database
            cursor.execute("SELECT timestamp, host, type, startDate, endDate, availability FROM website_alerts \
                WHERE timestamp > ? \
                ORDER BY timestamp ASC", fields)

        elif 'host' in queryData.keys():
            # If an hist was defined (by a Retriever, for example), get it
            fields = (queryData['host'],)

            # Query the database
            cursor.execute("SELECT timestamp, host, type, startDate, endDate, availability FROM website_alerts \
                WHERE host = ? \
                ORDER BY timestamp ASC", fields)

        else:
            # If nothing was precised, query the databse for all available data
            cursor.execute("SELECT timestamp, host, type, startDate, endDate, availability FROM website_alerts \
                ORDER BY timestamp ASC")

        # Return all results in an array
        result = cursor.fetchall()
        connection.close()
        return result

    if table == 'website_monitoring':
        # If the query concerns the website_alerts table
        # Get the host and the number of minutes for the search
        minutes = queryData['minutes']
        fields = (queryData['host'],)

        # Query the database
        cursor.execute("SELECT timestamp, available, status, responseTime FROM website_monitoring \
                WHERE host = ? AND datetime(timestamp) > datetime('now', '-{:d} minutes') \
                ORDER BY timestamp ASC".format(minutes), fields)

        # Return all results in an array
        result = cursor.fetchall()
        connection.close()
        return result

