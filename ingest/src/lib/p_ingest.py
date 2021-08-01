import boto3
import json
from datetime import datetime
from lib.a_ddb import AdptDynamoDB
from lib.a_s3 import AdptS3
from lib.a_sqs import AdptSQS
from lib.s_counter import SCounter
from lib.s_descriptor import Descriptor
from lib.s_encoders import DateTimeEncoder

class PortIngest:
    def __init__(self, config):
        self.session = boto3.session.Session()
        self.bucket = config["s3_bucket"]
        self.s3 = AdptS3(self.session, self.bucket)
        self.queue = config["sqs_queue"]
        self.sqs = AdptSQS(self.session, self.queue)
        self.counters_table = config["counters_table"]
        self.counters = SCounter(self.session, self.counters_table)

    def get(self, okey):
        ts_start = datetime.now()
        print(json.dumps({
            "bucket": self.bucket,
            "key": okey
        }))
        output = self.s3.get(self.bucket, okey).split("\n")
        ts_end = datetime.now()
        ts_duration = int((ts_end - ts_start).microseconds/1000)
        print(json.dumps({
            "ts_start": ts_start,
            "ts_end": ts_end,
            "duration_ms": ts_duration
        }, cls=DateTimeEncoder))
        return output

    def increment(self, eid, count):
        return self.counters.increment(eid, "ingested", count)

    def send_message_batch(self, batches):
        return self.sqs.send_message_batch(batches)
