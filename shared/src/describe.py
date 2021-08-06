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

    def process_execution_history(self, history):
        ts_start = 0
        details1 = ["stateEnteredEventDetails", "stateExitedEventDetails", "mapIterationStartedEventDetails", "mapIterationSucceededEventDetails"]
        details2 = ["lambdaFunctionScheduledEventDetails"]
        in_scope = ["TaskStateEntered", "TaskStateExited"]
        out_of_scope = ["ExecutionStarted",  "LambdaFunctionScheduled", "LambdaFunctionSucceeded", "MapStateEntered", "MapStateSucceeded", "MapIterationStarted", "MapIterationSucceeded"]
        output = {
            "ExecutionId": "TBD",
            "Processed": 0
        }
        for event in history:
            item = {k: event[k] for k in ["id", "timestamp"]}
            ts_current = event["timestamp"].timestamp()*1000
            if ts_start == 0:
                ts_start = ts_current
            item["elapsed"] = ts_current - ts_start
            item["type"] = event["type"]
            for detail in details1:
                if detail in event:
                    item[detail] = event[detail]["name"]
            for detail in details2:
                if detail in event:
                    item[detail] = event[detail]["resource"].split(":")[-1]
            if event["type"] == "TaskStateExited" and event["stateExitedEventDetails"]["name"] == "ReducePrep":
                payload = json.loads(event["stateExitedEventDetails"]["output"])
                output["ExecutionId"] = payload["eid"]
                output["Processed"] = payload["processed"]
            if event["type"] in in_scope:
                if item["type"] == "TaskStateEntered" and item["stateEnteredEventDetails"] not in output:
                    output[item["stateEnteredEventDetails"]] = {
                        "TaskStateEntered": item["elapsed"]
                    }
                if item["type"] == "TaskStateExited":
                    output[item["stateExitedEventDetails"]]["TaskStateExited"] = item["elapsed"]
        return output

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eid", required=True, help="execution id")
    args = ap.parse_args()
    d = Describe()
    history = d.get_execution_history(args.eid)
    # print(json.dumps(history, cls=DateTimeEncoder))
    output = d.process_execution_history(history)
    # print(json.dumps(output, cls=DateTimeEncoder))
    excel = [
        args.eid,
        output["ExecutionId"],
        output["Processed"],
        output["IngestForMap"]["TaskStateEntered"],
        output["IngestForMap"]["TaskStateExited"],
        output["ReducePrep"]["TaskStateEntered"],
        output["ReducePrep"]["TaskStateExited"],
        output["ReduceGate"]["TaskStateEntered"],
        output["ReduceGate"]["TaskStateExited"],
        output["ReduceAggregate"]["TaskStateEntered"],
        output["ReduceAggregate"]["TaskStateExited"],
        output["ReduceRank"]["TaskStateEntered"],
        output["ReduceRank"]["TaskStateExited"]
    ]
    print(json.dumps(excel))

if __name__ == "__main__":
    main()
