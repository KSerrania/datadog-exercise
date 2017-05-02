import requests
from datetime import timedelta, datetime

class Monitor():
    """Monitor class whose goal is to check the monitored website's availability and performance.

    Attributes:
        URL (str): URL of the monitored website.
        influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.

    """

    def __init__(self, URL, influxClient):
        """Sets the URL and influxDBClient as speficied in the parameters.

        Args:
            URL (str): URL of the monitored website.
            influxClient (InfluxDBClient): Client for the InfluxDB used to store monitoring data.

        """
        self.URL = URL
        self.influxClient = influxClient
        
    def __availabilityCheck(self):
        try:
            response = requests.get("http://{}".format(self.URL))
            return True, response
        except requests.Timeout as e:
            print('The request at {} timed out'.format(self.URL))
            return False, None
        except requests.ConnectionError as e:
            print('Error while connecting to {}'.format(self.URL))
            return False, None
        except requests.InvalidURL as e:
            print('Invalid URL for site {}'.format(self.URL))
            return False, None
        except Exception as e:
            print('There was an error while connecting to {}'.format(self.URL))
            return False, None


    def get(self):
        """Gets data about the monitored website and stores it into the InfluxDB database.

        """
        currentDate = str(datetime.now())
        available, response = self.__availabilityCheck()
        if available:
            responseTime = response.elapsed.total_seconds() * 1000
            status = response.status_code
        else:
            responseTime = None
            status = None
        data = [
            {
                "measurement": "website_availability",
                "tags": {
                    "host": self.URL    
                },
                "time": currentDate,
                "fields": {
                    "available": available,
                    "status": status,
                    "responseTime": responseTime
                }
            }
        ]
        self.influxClient.write_points(data)
