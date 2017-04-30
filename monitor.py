import requests
import subprocess
from datetime import datetime

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
        self.pingStats = []

    def get(self):
        """Gets data about the monitored website and stores it into the InfluxDB database

        """
        try:
            status = requests.get("http://{}".format(self.URL)).status_code
        except:
            status = 404

        try:
            pingResult = subprocess.run(['ping', '-c', '1', self.URL], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pingResult.check_returncode()
            ping = pingResult.stdout.decode('utf-8').split()
            pingTime = float(ping[12].split('=')[1])
        except subprocess.CalledProcessError:
            pingTime = None

        data = [
            {
                "measurement": "website_availability",
                "tags": {
                    "host": self.URL    
                },
                "time": str(datetime.now()),
                "fields": {
                    "status": status,
                    "latency": pingTime
                }
            }
        ]
        self.influxClient.write_points(data)
