import boto3
import csv
import json
import uuid
from datetime import datetime

# helper class
class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

# main class
class SReduce:
    def __init__(self, table, bucket):
        self.session = boto3.session.Session()
        self.cl_ddb = self.session.client("dynamodb")
        self.cl_s3 = self.session.client("s3")
        self.table = table
        self.bucket = bucket

    def get_object(self, bucket, key):
        response = self.cl_s3.get_object(
            Bucket=bucket,
            Key=key
        )
        # TODO: convert from reading entire file to handle streaming body
        return response["Body"].read().decode("utf-8").split("\n")

    def process(self, items):
        # prep aggregation
        aggregation = {}
        # group by eid and pk
        for eid in items:
            for pk in items[eid]:
                print("{}/{} -> {}".format(eid, pk, json.dumps(items[eid][pk])))
                # process items within a pk
                for item in items[eid][pk]:
                    body = self.get_object(self.bucket, "{}/{}/{}.json".format(eid, pk, item))
                    for row in body:
                        data = json.loads(row)
                        for datum in data:
                            # [FlightDate,UniqueCarrier,FlightNum,Origin,Dest,DepDelay,ArrDelay]
                            airline = datum[1]
                            arrdelay = datum[6]
                            if airline not in aggregation:
                                aggregation[airline] = {
                                    "total": 0,
                                    "count": 0
                                }
                            aggregation[airline]["total"] += float(arrdelay) if arrdelay != "" else 0
                            aggregation[airline]["count"] += 1
        # perform reduce operation
        output = []
        for airline in aggregation:
            output.append({
                "airline": pk,
                "arrdelay": aggregation[airline]["total"]/aggregation[airline]["count"]
            })
        output = sorted(output, key=lambda x: x["arrdelay"])
        return output
