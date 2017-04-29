from collections import Counter
from datetime import datetime

class Retriever():
    def __init__(self, URL, influxClient):
        self.URL = URL
        self.influxClient = influxClient
        self.alert = False
        self.alertNumber = 0

    def getStats(self, minutes):
        data = self.influxClient.query("SELECT latency, status FROM website_availability WHERE time > now() - {}m AND host = '{}'".format(minutes, self.URL)).raw
        if 'series' in data.keys():
            statusCodes = Counter([elt[2] if elt[2] is not None else 404 for elt in data['series'][0]['values']])
            latencies = [elt[1] for elt in data['series'][0]['values'] if elt[1] is not None]
        else:
            return False, {}

        n = sum(statusCodes.values())
        nLatencies = len(latencies)
        minLatency = min(latencies, default=float('inf'))
        maxLatency = max(latencies, default=float('inf'))
        try:
            avgLatency = sum(latencies) / nLatencies
        except:
            avgLatency = float('inf')

        pingResponse = nLatencies / n
        availability = statusCodes[200] / n
        return True, {
                'availability': availability,
                'statusCodes': statusCodes,
                'avgLatency': avgLatency,
                'minLatency': minLatency,
                'maxLatency': maxLatency,
                'pingResponse': pingResponse
                }
    
    def checkAlert(self):
        statusCodes = Counter([elt[1] for elt in self.influxClient.query("SELECT status FROM website_availability WHERE time > now() - 2m AND host = '{}'".format(self.URL)).raw['series'][0]['values']])
        n = sum(statusCodes.values())
        availability = statusCodes[200] / n
        
        if self.alert and availability > 0.8:
            return "\n\033[92mWebsite {} recovered from alert {}. Availability={:.2f}, time={}\033[0m".format(self.URL, availability, str(datetime.now()))

        if not(self.alert) and availability < 0.8:
            self.alertNumber += 1
            return "\n\033[91mWebsite {} is down. Availability={:.2f}, time={}. (Alert {})\033[0m".format(self.URL, availability, str(datetime.now(), self.alertNumber))
        return ""
