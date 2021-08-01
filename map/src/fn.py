import json
import os
from lib.s_map import SMap

# initialization
config = {
    "shuffle_type": os.getenv("SHUFFLE_TYPE", "s3"),
    "shuffle_table": os.environ["SHUFFLE_TABLE"],
    "shuffle_lsi": os.environ["SHUFFLE_LSI"],
    "shuffle_bucket": os.environ["SHUFFLE_BUCKET"],
    "counters_table": os.environ["COUNTERS_TABLE"]
}
s_map = SMap(config)

# lambda invoker handler
def handler(event, context):
    # print(json.dumps(event))
    output = {
        "mapped": []
    }
    for record in event["Records"]:
        body = json.loads(record["body"])
        eid = body["eid"]
        batch = body["batch"]
        response = s_map.process(eid, batch)
        output["eid"] = eid
        output["mapped"].extend(response["mapped"])
    return output
