import os
from lib.s_counter import SCounter
from lib.s_ingest import SIngest

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
def handler(event, context):
    eid = event["eid"]
    output = {
        "eid": eid,
        "ingested": []
    }
    for record in event["Records"]:
        if "s3" in record:
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
        else:
            bucket = record["bucket"]
            key = record["key"]
        s_ingest.process(eid, bucket, key, batch_size, limit)
        s_counters.increment(eid, "ingested")
        output["ingested"].append({
            "bucket": bucket,
            "key": key
        })
    return output

# initialization
table_counters = os.environ["TABLE_COUNTERS"]
queue = os.environ["QUEUE"]
batch_size = int(os.environ["BATCHSIZE"])
limit = int(os.environ["LIMIT"])
s_ingest = SIngest(queue)
s_counters = SCounter(table_counters)
