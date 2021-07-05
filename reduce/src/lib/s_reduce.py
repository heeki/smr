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

    def process(self, item):
        body = self.get_object(self.bucket, item)
        output = 0
        for line in body:
            data = json.loads(line)
            if data[11] == "BUF":
                output += 1
        return output
