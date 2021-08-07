import asyncio
import json
import os
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
# from codeguru_profiler_agent import with_lambda_profiler
from lib.s_counter import SCounter
from lib.s_ingest import SIngest

# initialization
config = {
    "counters_table": os.environ["COUNTERS_TABLE"],
    "s3_bucket": os.environ["BUCKET"],
    "sqs_queue": os.environ["SQS_QUEUE"],
    "sqs_batch_size": int(os.environ["SQS_BATCH_SIZE"]),
    "sqs_batch_limit": int(os.environ["SQS_BATCH_LIMIT"]),
    "num_tasks": int(os.environ["NUM_TASKS"])
}
print(json.dumps(config))
s_ingest = SIngest(config)

# initialization: codeguru
# profiling_group = os.environ["AWS_CODEGURU_PROFILER_GROUP_NAME"]

# lambda invoker handler
# @with_lambda_profiler(profiling_group_name=profiling_group)
def handler(event, context):
    s_ingest.initialize()
    eid = event["eid"]
    okey = event["key"]
    loop = asyncio.get_event_loop()
    processed = loop.run_until_complete(s_ingest.process(eid, okey))
    output = {
        "eid": eid,
        "key": okey,
        "processed": processed
    }
    print(json.dumps(output))
    return output
