import requests
import subprocess
from datetime import datetime

class Monitor():
    def __init__(self, URL, influxClient):
        self.URL = URL
        self.influxClient = influxClient
        self.pingStats = []

    def get(self):
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
