import json
import os
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

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
    output = {
        "processed": 0
    }
    for item in event:
        if "eid" not in output:
            output["eid"] = item["eid"]
        output["processed"] += item["processed"]
    print(json.dumps(output))
    return output

# initialization: xray
patch_all()
