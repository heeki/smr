import boto3
import json
from lib.a_ddb import AdptDynamoDB
from lib.a_s3 import AdptS3
from lib.s_counter import SCounter

class PortMap:
    def __init__(self, config):
        self.session = boto3.session.Session()
        self.shuffle_type = config["shuffle_type"]
        if self.shuffle_type == "s3":
            self.shuffle_bucket = config["shuffle_bucket"]
            self.client = AdptS3(self.session, self.shuffle_bucket)
        elif self.shuffle_type == "dynamodb":
            self.shuffle_table = config["shuffle_table"]
            self.client = AdptDynamoDB(self.session, self.shuffle_table)
        self.counters_table = config["counters_table"]
        self.counters = SCounter(self.session, self.counters_table)

    def put(self, desc, payload):
        if self.shuffle_type == "s3":
            item = json.dumps(payload)
            response = self.client.put(desc.get_s3_okey(), item)
        elif self.shuffle_type == "dynamodb":
            item = {
                "eid": {"S": desc.get_ddb_hkey()},
                "iid": {"S": desc.get_ddb_rkey()},
                "pk": {"S": desc.get_ddb_lsi_rkey()},
                "data": {"S": json.dumps(payload)}
            }
            response = self.client.put(item)
        return response

    def increment(self, eid, count):
        self.counters.increment(eid, "mapped", count)
