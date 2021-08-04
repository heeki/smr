import boto3
import json
import os.path
import uuid
from datetime import datetime

# helper class
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

class Trigger:
    def __init__(self):
        self.session = boto3.session.Session()
        self.cl_s3 = self.session.client("s3")
        self.cl_sf = self.session.client("stepfunctions")
        self.cl_lambda = self.session.client("lambda")
        if os.path.exists("etc/config.json"):
            with open("etc/config.json") as f:
                self.config = json.load(f)
                self.config["eid"] = str(uuid.uuid4())

    def list_objects(self):
        output = []
        response = self.cl_s3.list_objects_v2(
            Bucket=self.config["bucket"],
            Prefix=self.config["prefix_live"]
        )
        for item in response["Contents"]:
            if item["Key"].endswith(".csv"):
                output.append({
                    "eid": self.config["eid"],
                    "bucket": self.config["bucket"],
                    "key": item["Key"]
                })
        return output

    def invoke_fn(self, item):
        payload = {
            "eid": self.config["eid"],
            "bucket": self.config["bucket"],
            "key": item
        }
        response = self.cl_lambda.invoke(
            FunctionName=self.config["ingest_fn"],
            # InvocationType="RequestResponse",
            InvocationType="Event",
            LogType="None",
            Payload=json.dumps(payload)
        )
        return response

    def invoke_sfn(self, payload):
        arn = "arn:aws:states:us-east-1:{}:stateMachine:{}".format(self.config["account_id"], self.config["ingest_sfn"])
        response = self.cl_sf.start_execution(
            stateMachineArn=arn,
            input=json.dumps(payload)
        )
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
