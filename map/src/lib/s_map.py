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
class SMap:
    def __init__(self, table, bucket):
        self.session = boto3.session.Session()
        self.cl_ddb = self.session.client("dynamodb")
        self.cl_s3 = self.session.client("s3")
        self.table = table
        self.bucket = bucket

    def process(self, eid, item):
        print(json.dumps(item))
        okey = "{}/{}.json".format(eid, uuid.uuid4())
        response = self.cl_s3.put_object(
            Bucket=self.bucket,
            Body=json.dumps(item),
            Key=okey
        )
        print(response)
        return okey
