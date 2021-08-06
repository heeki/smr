import argparse
import boto3
import json
import os
from datetime import datetime
from python.lib.a_sfn import AdptSFn
from python.lib.s_encoders import DateTimeEncoder

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

def _validate(item, field1, field2):
    if field1 in item and field2 in item[field1]:
        return item[field1][field2]
    else:
        return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eid", required=True, help="execution id")
    ap.add_argument("--format", help="json, excel")
    args = ap.parse_args()
    d = Describe()
    history = d.get_execution_history(args.eid)
    output = d.process_execution_history(history)
    if args.format is not None and args.format == "excel":
        excel = [
            args.eid,
            output["ExecutionId"],
            output["Processed"],
            _validate(output, "IngestForMap", "TaskStateEntered"),
            _validate(output, "IngestForMap", "TaskStateExited"),
            _validate(output, "ReducePrep", "TaskStateEntered"),
            _validate(output, "ReducePrep", "TaskStateExited"),
            _validate(output, "ReduceGate", "TaskStateEntered"),
            _validate(output, "ReduceGate", "TaskStateExited"),
            _validate(output, "ReduceAggregate", "TaskStateEntered"),
            _validate(output, "ReduceAggregate", "TaskStateExited"),
            _validate(output, "ReduceRank", "TaskStateEntered"),
            _validate(output, "ReduceRank", "TaskStateExited")
        ]
        print(json.dumps(excel))
    else:
        print(json.dumps(output, cls=DateTimeEncoder))

if __name__ == "__main__":
    main()
