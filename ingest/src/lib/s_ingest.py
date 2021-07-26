import boto3
import botocore
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
class SIngest:
    def __init__(self, queue, batch_size=100, batch_limit=1):
        # boto3 clients
        self.session = boto3.session.Session()
        self.cl_s3 = self.session.client("s3")
        self.cl_sqs = self.session.client("sqs")
        # parameters
        self.queue = queue
        self.batch_size = batch_size
        self.batch_limit = batch_limit
        # internal data
        self.group_id = str(uuid.uuid4())
        self.messages = []
        self.batches = []
        self.i_messages = 0
        self.i_batches = 0

    # get data file from s3
    def get_object(self, bucket, key):
        ts_start = datetime.now()
        print(json.dumps({
            "bucket": bucket,
            "key": key
        }))
        response = self.cl_s3.get_object(
            Bucket=bucket,
            Key=key
        )
        # TODO: convert from reading entire file to handle streaming body
        try:
            output = response["Body"].read().decode("utf-8").split("\n")
        except Exception as e:
            print(e)
            output = response["Body"].read().decode("latin-1").split("\n")
        ts_end = datetime.now()
        ts_duration = int((ts_end - ts_start).microseconds/1000)
        print(json.dumps({
            "ts_start": ts_start,
            "ts_end": ts_end,
            "duration_ms": ts_duration
        }, cls=DateTimeEncoder))
        return output

    # enqueue message into batch
    def enqueue_message(self, eid, message):
        self.messages.append(message)
        self.i_messages += 1
        # log processing status
        if self.i_messages % 10000 == 0:
            print(json.dumps({
                "ts": datetime.now(),
                "processed": self.i_messages
            }, cls=DateTimeEncoder))
        # if batch is full, enqueue the batch and reset it
        if len(self.messages) == self.batch_size:
            self.enqueue_batch(eid)
            self.messages = []

    # enqueue batch into entries for bulk send to sqs
    def enqueue_batch(self, eid):
        self.batches.append({
            "Id": str(uuid.uuid4()),
            "MessageBody": json.dumps({
                "eid": eid,
                "batch": self.messages
            })
        })
        self.i_batches += 1
        if len(self.batches) == 4:
            self.send_message_batch()
            self.batches = []

    # bulk send to sqs
    def send_message_batch(self):
        try:
            response = self.cl_sqs.send_message_batch(
                QueueUrl=self.queue,
                Entries=self.batches
            )
        except botocore.exceptions.ClientError as e:
            print(e)
            half = len(self.batches)//2
            a = self.batches[:half]
            b = self.batches[half:]
            response = []
            if len(a) > 0:
                response.append(self.cl_sqs.send_message_batch(
                    QueueUrl=self.queue,
                    Entries=a
                ))
            if len(b) > 0:
                response.append(self.cl_sqs.send_message_batch(
                    QueueUrl=self.queue,
                    Entries=b
                ))
        return response

    # process data file, emit to sqs
    def process(self, eid, bucket, key):
        # get data file
        subsegment = xray_recorder.begin_subsegment("S3 GetObject")
        subsegment.put_annotation("ExecutionId", eid)
        body = self.get_object(bucket, key)
        xray_recorder.end_subsegment()
        # process data file
        subsegment = xray_recorder.begin_subsegment("SQS SendMessages")
        subsegment.put_annotation("ExecutionId", eid)
        for line in body:
            reader = csv.reader([line], delimiter=",")
            parsed = list(reader)[0]
            # skip empty lines and the header, otherwise add message to batch
            if len(parsed) == 0:
                continue
            if parsed[0] == "Year":
                continue
            self.enqueue_message(eid, parsed)
            # check if exceeded batch limit
            if self.batch_limit > 0 and self.i_batches == self.batch_limit:
                break
        # if needed, send last of the data
        if len(self.messages) > 0:
            self.enqueue_batch(eid)
        if len(self.batches) < 4:
            self.send_message_batch()
        xray_recorder.end_subsegment()
        return self.i_messages
