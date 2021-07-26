import boto3
import csv
import json
import uuid
from aws_xray_sdk.core import xray_recorder
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

    def list_prefixes(self, eid):
        response = self.cl_s3.list_objects(
            Bucket=self.bucket,
            Prefix="{}/".format(eid),
            Delimiter="/"
        )
        output = []
        for prefix in response["CommonPrefixes"]:
            output.append(prefix["Prefix"])
        return output

    def list_objects(self, prefix):
        paginator = self.cl_s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(
            Bucket=self.bucket,
            Prefix=prefix
        )
        output = []
        for page in pages:
            for content in page["Contents"]:
                output.append(content["Key"])
        return output

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
        subsegment = xray_recorder.begin_subsegment("Reduce Phase")
        is_first = True
        for item in items:
            (eid, pk, iid) = item.split(".")[0].split("/")
            if is_first:
                subsegment.put_annotation("ExecutionId", eid)
                is_first = False
            body = self.get_object(self.bucket, item)
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
        output = {
            "eid": eid,
            "airline": pk,
            "total": aggregation[airline]["total"],
            "count": aggregation[airline]["count"],
            "arrdelay": aggregation[airline]["total"]/aggregation[airline]["count"]
        }
        xray_recorder.end_subsegment()
        return output

    def aggregate(self, items):
        output = [{"airline": item["airline"], "arrdelay": item["arrdelay"]} for item in items]
        output = sorted(output, key=lambda x: x["arrdelay"])
        return output
