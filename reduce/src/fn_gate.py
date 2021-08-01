import json
import os
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from lib.s_reduce import SReduce

# initialization: xray
patch_all()

# initialization
config = {
    "shuffle_type": os.getenv("SHUFFLE_TYPE", "s3"),
    "shuffle_table": os.environ["SHUFFLE_TABLE"],
    "shuffle_lsi": os.environ["SHUFFLE_LSI"],
    "shuffle_bucket": os.environ["SHUFFLE_BUCKET"],
    "counters_table": os.environ["COUNTERS_TABLE"]
}
s_reduce = SReduce(config)

# lambda invoker handler
def handler(event, context):
    print(json.dumps(event))
    eid = event["eid"]
    output = s_reduce.is_ready(eid)
    return output
