import requests
import subprocess
from datetime import datetime

class Monitor():
    def __init__(self, URL, influxClient):
        self.URL = URL
        self.influxClient = influxClient
        self.pingStats = []

    def get(self):
        print(self.URL)
        try:
            status = requests.get("http://{}".format(self.URL)).status_code
        except:
            status = 404

        try:
            ping = subprocess.check_output(['ping', '-c', '1', self.URL]).split()
            pingTime = float(ping[12].decode('utf-8').split('=')[1])
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
        print(data)
        self.influxClient.write_points(data)
