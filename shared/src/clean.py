import argparse
import boto3
import json
import os
from datetime import datetime
from python.lib.a_ddb import AdptDynamoDB
from python.lib.a_s3 import AdptS3

# helper class
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

class Clean:
    def __init__(self):
        self.session = boto3.session.Session()
        if os.path.exists("etc/config.json"):
            with open("etc/config.json") as f:
                self.config = json.load(f)
        self.ddb = AdptDynamoDB(self.session, self.config["shuffle_table"])
        self.s3 = AdptS3(self.session, self.config["shuffle_bucket"])

    def clean_s3(self, eid):
        return {}

    def _trim_response(self, response):
        output = response
        if "ResponseMetadata" in response:
            del output["ResponseMetadata"]["RequestId"]
            del output["ResponseMetadata"]["HTTPStatusCode"]
            del output["ResponseMetadata"]["HTTPHeaders"]
        return output

    def clean_ddb(self, eid):
        expression_values = {
            ":eid": {"S": eid}
        }
        key_condition = "eid = :eid"
        projection_expression = "eid, iid"
        to_process = self.ddb.query(expression_values, key_condition, projection_expression)
        while len(to_process) > 25:
            to_delete = [{"hval": i["eid"]["S"], "sval": i["iid"]["S"]} for i in to_process][0:25]
            to_process = to_process[25:]
            response = self.ddb.batch_delete("eid", "iid", to_delete)
            print(json.dumps(self._trim_response(response), cls=DateTimeEncoder))
            if self.config["shuffle_table"] in response["UnprocessedItems"]:
                for unprocessed in response["UnprocessedItems"][self.config["shuffle_table"]]:
                    to_process.append(unprocessed["DeleteRequest"]["Key"])
        if len(to_process) > 0:
            to_delete = [{"hval": i["eid"]["S"], "sval": i["iid"]["S"]} for i in to_process]
            response = self.ddb.batch_delete("eid", "iid", to_delete)
            del response["ResponseMetadata"]
            print(json.dumps(self._trim_response(response), cls=DateTimeEncoder))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eid", required=True, help="execution id")
    args = ap.parse_args()
    clean = Clean()
    clean.clean_ddb(args.eid)

if __name__ == "__main__":
    main()
