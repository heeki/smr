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
    eid = event["eid"]
    # c_ingested = s_counter.get(eid, "ingested")
    # c_mapped = s_counter.get(eid, "mapped")
    is_ready = s_counter.check_ready(eid)
    output = {
        "eid": eid,
        # "ingested": c_ingested,
        # "mapped": c_mapped
        "is_ready": is_ready
    }
    print(json.dumps(output))
    return output

# initialization
table_counters = os.environ["TABLE_COUNTERS"]
table_shuffle = os.environ["TABLE_SHUFFLE"]
s_counter = SCounter(table_counters)
s_reduce = SReduce(table_shuffle)
