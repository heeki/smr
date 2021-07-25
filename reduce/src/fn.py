import json
import os
from lib.s_counter import SCounter
from lib.s_reduce import SReduce

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
    print(json.dumps(event))
    output = []
    if "mapped" in event:
        mapped = event["mapped"]
    else:
        mapped = []
    items = {}
    for item in mapped:
        (eid, pk, iid) = item.split(".")[0].split("/")
        if eid not in items:
            items[eid] = {}
        if pk not in items[eid]:
            items[eid][pk] = []
        items[eid][pk].append(iid)
    output = s_reduce.process(items)
    return output

# initialization
table_counters = os.environ["TABLE_COUNTERS"]
table_shuffle = os.environ["TABLE_SHUFFLE"]
bucket_shuffle = os.environ["BUCKET_SHUFFLE"]
s_counter = SCounter(table_counters)
s_reduce = SReduce(table_shuffle, bucket_shuffle)
