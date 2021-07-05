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
class SIngest:
    def __init__(self, queue):
        self.session = boto3.session.Session()
        self.cl_s3 = self.session.client("s3")
        self.cl_sqs = self.session.client("sqs")
        self.queue = queue
        self.group_id = str(uuid.uuid4())

    def get_object(self, bucket, key):
        response = self.cl_s3.get_object(
            Bucket=bucket,
            Key=key
        )
        # TODO: convert from reading entire file to handle streaming body
        return response["Body"].read().decode("utf-8").split("\n")

    def send_message(self, message):
        message_id = str(uuid.uuid4())
        response = self.cl_sqs.send_message(
            QueueUrl=self.queue,
            MessageBody=message,
            MessageDeduplicationId=message_id,
            MessageGroupId=self.group_id
        )
        return response

    def process(self, bucket, key, batch_size=10, limit=1):
        body = self.get_object(bucket, key)
        batch = []
        i_batch = 0
        i_limit = 0
        for line in body:
            reader = csv.reader([line], delimiter=",")
            parsed = list(reader)[0]
            if parsed[0] != "Year":
                batch.append(parsed)
                i_batch += 1
            if i_batch == batch_size:
                print(json.dumps(batch))
                self.send_message(json.dumps(batch))
                batch = []
                i_batch = 0
                i_limit += 1
                if i_limit == limit:
                    break
