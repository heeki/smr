import json
import os
from lib.s_counter import SCounter
from lib.s_map import SMap

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
    output = {
        "mapped": []
    }
    for record in event["Records"]:
        body = json.loads(record["body"])
        eid = body["eid"]
        batch = body["batch"]
        output["eid"] = eid
        for item in batch:
            okey = s_map.process(eid, item)
            output["mapped"].append(okey)
        s_counters.increment(eid, "mapped")
    return output

# initialization
table_counters = os.environ["TABLE_COUNTERS"]
table_shuffle = os.environ["TABLE_SHUFFLE"]
bucket_shuffle = os.environ["BUCKET_SHUFFLE"]
s_counters = SCounter(table_counters)
s_map = SMap(table_shuffle, bucket_shuffle)
