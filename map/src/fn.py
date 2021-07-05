import json
import os
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
    output = []
    for record in event["Records"]:
        message_id = record["messageId"]
        output.append({
            "message_id": message_id
        })
        body = json.loads(record["body"])
        for item in body:
            s_map.process(item)
    return output

# initialization
table = os.environ["TABLE"]
s_map = SMap(table)
