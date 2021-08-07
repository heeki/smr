import asyncio
import csv
import json
import os
import uuid
from aws_xray_sdk.core import xray_recorder
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from lib.p_ingest import PortIngest
from lib.s_encoders import DateTimeEncoder

class SIngest:
    def __init__(self, config):
        self.port = PortIngest(config)
        self.batch_size = config["sqs_batch_size"]
        self.batch_limit = config["sqs_batch_limit"]
        self.num_tasks = config["num_tasks"]
        self.group_id = str(uuid.uuid4())
        self.enable_xray = "AWS_LAMBDA_INITIALIZATION_TYPE" in os.environ
        print("enable_xray={}".format(self.enable_xray))
        self.initialize()

    def initialize(self):
        self.messages = {}
        self.batches = {}
        self.i_messages = {}
        self.i_batches = {}

    # enqueue message into batch
    def enqueue_message(self, rid, eid, message):
        self.messages[rid].append(message)
        self.i_messages[rid] += 1
        # log processing status
        if self.i_messages[rid] % 10000 == 0:
            print(json.dumps({
                "ts": datetime.now(),
                "rid": rid,
                "processed": self.i_messages[rid]
            }, cls=DateTimeEncoder))
        # if batch is full, enqueue the batch and reset it
        if len(self.messages[rid]) == self.batch_size:
            self.enqueue_batch(rid, eid)
            self.messages[rid] = []

    # enqueue batch into entries for bulk send to sqs
    def enqueue_batch(self, rid, eid):
        self.batches[rid].append({
            "Id": str(uuid.uuid4()),
            "MessageBody": json.dumps({
                "eid": eid,
                "batch": self.messages[rid]
            })
        })
        self.i_batches[rid] += 1
        if len(self.batches[rid]) == 4:
            self.port.send_message_batch(self.batches[rid])
            self.batches[rid] = []

    def _split(self, items, num_splits):
        output = []
        for i in range(num_splits):
            output.append(items[i::num_splits])
        return output

    def _process(self, rid, eid, body):
        # initialize thread variables
        self.messages[rid] = []
        self.batches[rid] = []
        self.i_messages[rid] = 0
        self.i_batches[rid] = 0
        # process data file
        if self.enable_xray:
            subsegment = xray_recorder.begin_subsegment("SQS SendMessages")
            subsegment.put_annotation("ExecutionId", eid)
            subsegment.put_annotation("TaskId", rid)
        for line in body:
            reader = csv.reader([line], delimiter=",")
            parsed = list(reader)[0]
            # skip empty lines and the header, otherwise add message to batch
            if len(parsed) == 0:
                continue
            if parsed[0] == "Year":
                continue
            self.enqueue_message(rid, eid, parsed)
            # check if exceeded batch limit
            if self.batch_limit > 0 and self.i_batches[rid] == self.batch_limit:
                break
        # if needed, send last of the data
        if len(self.messages[rid]) > 0:
            self.enqueue_batch(rid, eid)
        if len(self.batches[rid]) > 0 and len(self.batches[rid]) < 4:
            self.port.send_message_batch(self.batches[rid])
        if self.enable_xray:
            xray_recorder.end_subsegment()
        return self.i_messages[rid]

    # process data file, emit to sqs
    async def process(self, eid, okey):
        # get data file
        if self.enable_xray:
            subsegment = xray_recorder.begin_subsegment("S3 GetObject")
            subsegment.put_annotation("ExecutionId", eid)
        body = self.port.get(okey)
        if self.enable_xray:
            xray_recorder.end_subsegment()

        # process split row
        splits = self._split(body, self.num_tasks)

        # multiprocessing spawns multiple processes
        with ThreadPoolExecutor(max_workers=self.num_tasks) as executor:
            loop = asyncio.get_event_loop()
            tasks = [loop.run_in_executor(executor, self._process, *(rid, eid, splits[rid])) for rid in range(self.num_tasks)]
            for response in await asyncio.gather(*tasks):
                self.port.increment(eid, response)

        # asyncio is inhibited by gil (if using this snippet, need to switch _process() to async)
        # tasks = [asyncio.create_task(self._process(rid, eid, splits[rid])) for rid in range(self.num_tasks)]
        # for response in await asyncio.gather(*tasks):
        #     self.port.increment(eid, response)

        # calc total processed rows
        total = 0
        for rid in self.i_messages:
            total += self.i_messages[rid]
        return total
