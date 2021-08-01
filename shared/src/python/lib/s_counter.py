import boto3
import botocore
from lib.a_ddb import AdptDynamoDB

class SCounter:
    def __init__(self, session, table):
        self.client = AdptDynamoDB(session, table)

    def get(self, eid, attr):
        hkey = {
            "id": {"S": eid}
        }
        item = self.client.get(hkey)
        if attr in item:
            return int(item[attr]["N"])
        else:
            return -1

    def increment(self, eid, attr, incr=1):
        hkey = {
            "id": {"S": eid}
        }
        return self.client.increment(hkey, attr, incr)

    def is_ready(self, eid):
        hkey = {
            "id": {"S": eid}
        }
        item = self.client.get(hkey)
        if "ingested" in item and "mapped" in item and int(item["ingested"]["N"]) == int(item["mapped"]["N"]):
            return True
        else:
            return False
