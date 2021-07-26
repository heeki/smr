import json
import os
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
    mapped = s_reduce.list_objects(event)
    output = s_reduce.process(mapped)
    return output

# initialization
table_shuffle = os.environ["TABLE_SHUFFLE"]
bucket_shuffle = os.environ["BUCKET_SHUFFLE"]
s_reduce = SReduce(table_shuffle, bucket_shuffle)
