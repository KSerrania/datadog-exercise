from collections import Counter
from datetime import datetime

class Retriever():
    def __init__(self, URL, influxClient):
        self.URL = URL
        self.influxClient = influxClient
        self.alert = False
        self.alertNumber = 0

    def getStats(self, minutes):
        statusCodes = Counter([elt[1] for elt in self.influxClient.query("SELECT status FROM website_availability WHERE time > now() - {}m AND host = '{}'".format(minutes, self.URL)).raw['series'][0]['values']])
        latencies = self.influxClient.query("SELECT latency FROM website_availability WHERE time > now() - {}m AND host = '{}'".format(minutes, self.URL)).raw
        if 'series' in latencies.keys():
            latencies = [elt[1] for elt in latencies['series'][0]['values'] if elt[1] is not None]
        else:
            print(latencies)
        n = sum(statusCodes.values())
        nLatencies = len(latencies)
        avgLatency = sum(latencies) / nLatencies
        minLatency = min(latencies)
        maxLatency = min(latencies)
        pingResponse = nLatencies / n
        availability = statusCodes[200] / n
        return {
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
