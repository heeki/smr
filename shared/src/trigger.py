import boto3
import json
import os.path
import uuid
from datetime import datetime
from python.lib.a_lambda import AdptLambda
from python.lib.a_s3 import AdptS3
from python.lib.a_sfn import AdptSFn

# helper class
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

class Trigger:
    def __init__(self):
        self.session = boto3.session.Session()
        self.cl_lambda = self.session.client("lambda")
        if os.path.exists("etc/config.json"):
            with open("etc/config.json") as f:
                self.config = json.load(f)
                self.config["eid"] = str(uuid.uuid4())
        self.fn = AdptLambda(self.session)
        self.s3 = AdptS3(self.session, self.config["bucket"])
        self.sfn = AdptSFn(self.session, self.config["account_id"])

    def list_objects(self):
        output = []
        response = self.s3.list_objects(self.config["prefix_live"])
        for item in response:
            if item.endswith(".csv"):
                output.append({
                    "eid": self.config["eid"],
                    "bucket": self.config["bucket"],
                    "key": item
                })
        return output

    def invoke_fn(self, item):
        payload = {
            "eid": self.config["eid"],
            "bucket": self.config["bucket"],
            "key": item
        }
        response = self.fn.invoke(self.config["ingest_fn"], payload, invoke_type="Event")
        return response

    def invoke_sfn(self, payload):
        response = self.sfn.invoke(self.config["ingest_sfn"], payload)
        return response

    def execute(self):
        items = self.list_objects()
        payload = {
            "input": []
        }
        for item in items[0:self.config["num_files"]]:
            payload["input"].append(item)
        response = self.invoke_sfn(payload)
        return response

# main
def main():
    trigger = Trigger()
    response = trigger.execute()
    print(json.dumps(response, cls=DateTimeEncoder))

if __name__ == "__main__":
    main()
