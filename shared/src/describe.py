import argparse
import boto3
import json
import os
from datetime import datetime
from python.lib.a_sfn import AdptSFn

# helper class
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

class Describe:
    def __init__(self):
        self.session = boto3.session.Session()
        if os.path.exists("etc/config.json"):
            with open("etc/config.json") as f:
                self.config = json.load(f)
        self.sfn = AdptSFn(self.session, self.config["account_id"])

    def describe_execution(self, eid):
        response = self.sfn.describe_execution(self.config["ingest_sfn"], eid)
        return response

    def get_execution_history(self, eid):
        response = self.sfn.get_execution_history(self.config["ingest_sfn"], eid)
        return response

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eid", required=True, help="execution id")
    args = ap.parse_args()
    d = Describe()
    events = d.get_execution_history(args.eid)
    ts_start = 0
    details1 = ["stateEnteredEventDetails", "stateExitedEventDetails", "mapIterationStartedEventDetails", "mapIterationSucceededEventDetails"]
    details2 = ["lambdaFunctionScheduledEventDetails"]
    in_scope = ["TaskStateEntered", "TaskStateExited"]
    out_of_scope = ["ExecutionStarted",  "LambdaFunctionScheduled", "LambdaFunctionSucceeded", "MapStateEntered", "MapStateSucceeded", "MapIterationStarted", "MapIterationSucceeded"]
    result = {}
    for event in events:
        output = {k: event[k] for k in ["id", "timestamp"]}
        ts_current = event["timestamp"].timestamp()*1000
        if ts_start == 0:
            ts_start = ts_current
        output["elapsed"] = ts_current - ts_start
        output["type"] = event["type"]
        for detail in details1:
            if detail in event:
                output[detail] = event[detail]["name"]
        for detail in details2:
            if detail in event:
                output[detail] = event[detail]["resource"].split(":")[-1]
        if event["type"] in in_scope:
            if output["type"] == "TaskStateEntered" and output["stateEnteredEventDetails"] not in result:
                result[output["stateEnteredEventDetails"]] = {
                    "TaskStateEntered": output["elapsed"]
                }
            if output["type"] == "TaskStateExited":
                result[output["stateExitedEventDetails"]]["TaskStateExited"] = output["elapsed"]
            # print(json.dumps(output, cls=DateTimeEncoder))
    print(json.dumps(result, cls=DateTimeEncoder))

if __name__ == "__main__":
    main()
