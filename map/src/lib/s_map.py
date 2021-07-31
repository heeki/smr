from aws_xray_sdk.core import xray_recorder
from lib.p_map import PortMap
from lib.s_descriptor import Descriptor
from lib.s_encoders import DateTimeEncoder

class SMap:
    def __init__(self, config):
        self.port = PortMap(config)

    def process(self, eid, batch):
        payload = {}
        i_messages = 0
        subsegment = xray_recorder.begin_subsegment("Map Phase")
        subsegment.put_annotation("ExecutionId", eid)
        for item in batch:
            pk = item[6]
            if pk not in payload:
                payload[pk] = []
            # [FlightDate,UniqueCarrier,FlightNum,Origin,Dest,DepDelay,ArrDelay]
            projection = [5,6,10,11,17,25,36]
            projected = [item[i] for i in projection]
            payload[pk].append(projected)
            i_messages += 1
        output = {
            "mapped": [],
            "processed": i_messages
        }
        for pk in payload:
            desc = Descriptor(eid, pk)
            response = self.port.put(desc, payload[pk])
            if response == 200:
                output["mapped"].append(str(desc))
        xray_recorder.end_subsegment()
        return output
