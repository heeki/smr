import json
import uuid

class Descriptor:
    def __init__(self, eid, pk):
        self.eid = eid
        self.pk = pk
        self.iid = str(uuid.uuid4())

    def __str__(self):
        return "{}/{}/{}".format(self.eid, self.pk, self.iid)

    def get_s3_okey(self):
        return "{}/{}/{}.json".format(self.eid, self.pk, self.iid)

    def get_ddb_hash_key(self):
        return "{}/{}".format(self.eid, self.pk)

    def get_ddb_range_key(self):
        return self.iid
