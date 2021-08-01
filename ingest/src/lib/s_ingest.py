import csv
import json
import uuid
from aws_xray_sdk.core import xray_recorder
from datetime import datetime
from lib.p_ingest import PortIngest
from lib.s_encoders import DateTimeEncoder

class SIngest:
    def __init__(self, config):
        self.port = PortIngest(config)
        # parameters
        self.batch_size = config["sqs_batch_size"]
        self.batch_limit = config["sqs_batch_limit"]
        # internal data
        self.group_id = str(uuid.uuid4())
        self.messages = []
        self.batches = []
        self.i_messages = 0
        self.i_batches = 0

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
            self.port.send_message_batch(self.batches)
            self.batches = []

    # process data file, emit to sqs
    def process(self, eid, okey):
        # get data file
        subsegment = xray_recorder.begin_subsegment("S3 GetObject")
        subsegment.put_annotation("ExecutionId", eid)
        body = self.port.get(okey)
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
            self.port.send_message_batch(self.batches)
        # increment counter
        self.port.increment(eid, self.i_messages)
        xray_recorder.end_subsegment()
        return self.i_messages
