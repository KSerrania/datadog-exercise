import requests
from dbutils import insertValue
from datetime import timedelta, datetime

class Monitor():
    """Class whose goal is to check the monitored website's availability and performance.

    Attributes:
        URL (str): URL of the monitored website,
        dbName (str): Name of the database to use.

    """

    def __init__(self, URL, dbName="monitoring.db"):
        """Sets the URL and database name as speficied in the parameters.

        Args:
            URL (str): URL of the monitored website,
            dbName (str): Name of the database to use.

        """

        self.URL = URL
        self.dbName = dbName

    def __availabilityCheck(self):
        """Checks if the monitored website is available by sending it a GET request.
        We define that a site is available if it responds to a GET request with a status code which
        doesn't start with 4 or 5.

        Returns:
            A tuple containing:
                - a boolean (False if the site is not available, True if it is),
                - a requests.Response object containing data about the requests, or None if the website
                  didn't answer the request.
        """

        try:
            # Send a request to the website, and verify that it doesn't respond with an error code
            response = requests.get(self.URL)
            if response.status_code < 400:
                return True, response
            else:
                return False, response
        # If the website doesn't respond, set that it is not available
        except requests.Timeout as e:
            #print('The request at {} timed out'.format(self.URL))
            return False, None
        except requests.ConnectionError as e:
            #print('Error while connecting to {}'.format(self.URL))
            return False, None
        except requests.InvalidURL as e:
            #print('Invalid URL for site {}'.format(self.URL))
            return False, None
        except Exception as e:
            #print('There was an error while connecting to {}'.format(self.URL))
            return False, None


    def get(self):
        """Gets data about the monitored website and stores it into the database.

        """

        # Get the current date to use it as a timestamp
        currentDate = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # Query the website
        available, response = self.__availabilityCheck()

        if response is not None:
            # If there was a response, get interesting fields about the response
            responseTime = response.elapsed.total_seconds() * 1000
            status = response.status_code
        else:
            # If not, fill the blanks with None
            responseTime = None
            status = None

        # Format data and write it to the database
        insertData = {
            "timestamp": currentDate,
            "host": self.URL,
            "available": available,
            "status": status,
            "responseTime": responseTime
        }
        insertValue(self.dbName, 'website_monitoring', insertData)
