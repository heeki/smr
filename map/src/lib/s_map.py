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

    def write_ddb(self, eid, pk, data):
        # TODO: will need to handle throttling errors
        response = self.cl_ddb.put_item(
            TableName=self.table,
            Item={
                "eid": {"S": "{}/{}".format(eid, pk)},
                "iid": {"S": str(uuid.uuid4())},
                "data": {"S": json.dumps(data)}
            }
        )
        return response["ResponseMetadata"]["HTTPStatusCode"]

    def write_s3(self, okey, data):
        response = self.cl_s3.put_object(
            Bucket=self.bucket,
            Key=okey,
            Body=json.dumps(data)
        )
        return response["ResponseMetadata"]["HTTPStatusCode"]

    def process(self, eid, batch):
        payload = {}
        for item in batch:
            pk = item[6]
            if pk not in payload:
                payload[pk] = []
            # [FlightDate,UniqueCarrier,FlightNum,Origin,Dest,DepDelay,ArrDelay]
            projection = [5,6,10,11,17,25,36]
            projected = [item[i] for i in projection]
            payload[pk].append(projected)
        output = []
        for pk in payload:
            okey = "{}/{}/{}.json".format(eid, pk, uuid.uuid4())
            response = self.write_s3(okey, payload[pk])
            # response = self.write_ddb(eid, pk, projected)
            if response == 200:
                output.append(okey)
        return output