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
    def __init__(self, table):
        self.session = boto3.session.Session()
        self.cl_s3 = self.session.client("dynamodb")
        self.table = table

    def process(self, item):
        print(json.dumps(item))
