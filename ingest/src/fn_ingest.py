import json
import os
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from codeguru_profiler_agent import with_lambda_profiler
from lib.s_counter import SCounter
from lib.s_ingest import SIngest

# initialization: global variables
batch_size = int(os.environ["BATCH_SIZE"])
batch_limit = int(os.environ["BATCH_LIMIT"])

# initialization: sqs
queue = os.environ["QUEUE"]

# initialization: ddb
profiling_group = os.environ["AWS_CODEGURU_PROFILER_GROUP_NAME"]
table_counters = os.environ["TABLE_COUNTERS"]
s_counters = SCounter(table_counters)

# helper functions
def build_response(code, body):
    # headers for cors
    headers = {
        "Access-Control-Allow-Origin": "amazonaws.com",
        "Access-Control-Allow-Credentials": True
    }
    # lambda proxy integration
    response = {
        'isBase64Encoded': False,
        'statusCode': code,
        'headers': headers,
        'body': body
    }
    return response

def get_method(event):
    response = None
    context = event["requestContext"]
    # version 1.0
    if "httpMethod" in context:
        response = context["httpMethod"]
    # version 2.0
    elif "http" in context and "method" in context["http"]:
        response = context["http"]["method"]
    return response

# lambda invoker handler
@with_lambda_profiler(profiling_group_name=profiling_group)
def handler(event, context):
    eid = event["eid"]
    bucket = event["bucket"]
    okey = event["key"]
    s_ingest = SIngest(queue, batch_size=batch_size, batch_limit=batch_limit)
    processed = s_ingest.process(eid, bucket, okey)
    s_counters.increment(eid, "ingested", processed)
    output = {
        "eid": eid,
        "bucket": bucket,
        "key": okey,
        "processed": processed
    }
    print(json.dumps(output))
    return output
