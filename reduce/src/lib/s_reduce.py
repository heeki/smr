from aws_xray_sdk.core import xray_recorder
from lib.p_reduce import PortReduce
from lib.s_descriptor import Descriptor
# from lib.s_encoders import DateTimeEncoder

class SReduce:
    def __init__(self, config):
        self.port = PortReduce(config)

    def is_ready(self, eid):
        is_ready = self.port.is_ready(eid)
        output = {}
        output["eid"] = eid
        output["is_ready"] = is_ready
        if is_ready:
            output["mapped"] = self.port.list_tier2(eid)
        return output

    def process(self, eid, pk):
        # mapping
        mapping = {
            "FlightDate": 0,
            "UniqueCarrier": 1,
            "FlightNum": 2,
            "Origin": 3,
            "Dest": 4,
            "DepDelay": 5,
            "ArrDelay": 6
        }
        # prep aggregation
        subsegment = xray_recorder.begin_subsegment("DynamoDB Get")
        subsegment.put_annotation("ExecutionId", eid)
        items = self.port.list_tier3(eid, pk)
        xray_recorder.end_subsegment()
        aggregation = {}
        subsegment = xray_recorder.begin_subsegment("Reduce Phase")
        subsegment.put_annotation("ExecutionId", eid)
        for item in items:
            (eid, pk, iid) = Descriptor.from_s3_okey(item)
            body = self.port.get(eid, pk, iid)
            for datum in body:
                airline = datum[mapping["UniqueCarrier"]]
                arrdelay = datum[mapping["ArrDelay"]]
                if airline not in aggregation:
                    aggregation[airline] = {
                        "total": 0,
                        "count": 0
                    }
                aggregation[airline]["total"] += float(arrdelay) if arrdelay != "" else 0
                aggregation[airline]["count"] += 1
        # perform reduce operation
        output = {
            "eid": eid,
            "airline": pk,
            "total": aggregation[airline]["total"],
            "count": aggregation[airline]["count"],
            "arrdelay": aggregation[airline]["total"]/aggregation[airline]["count"]
        }
        xray_recorder.end_subsegment()
        return output

    def aggregate(self, items):
        output = [{"airline": item["airline"], "arrdelay": item["arrdelay"]} for item in items]
        output = sorted(output, key=lambda x: x["arrdelay"])
        return output
