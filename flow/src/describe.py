import argparse
import boto3
import json
import os
from datetime import datetime

# helper class
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

class Describe:
    def __init__(self):
        self.session = boto3.session.Session()
        self.client = self.session.client("stepfunctions")
        if os.path.exists("etc/config.json"):
            with open("etc/config.json") as f:
                self.config = json.load(f)

    def describe_execution(self, eid):
        arn = "arn:aws:states:us-east-1:{}:execution:{}:{}".format(self.config["account_id"], self.config["ingest_sfn"], eid)
        response = self.client.describe_execution(
        # response = self.client.describe_state_machine_for_execution(
            executionArn=arn,
        )
        return response

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eid", required=True, help="execution id")
    args = ap.parse_args()
    d = Describe()
    response = d.describe_execution(args.eid)
    print(json.dumps(response, cls=DateTimeEncoder))

if __name__ == "__main__":
    main()
