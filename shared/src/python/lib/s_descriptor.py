import uuid

class Descriptor:
    def __init__(self, eid, pk, iid=None):
        self.eid = eid
        self.pk = pk
        if iid is None:
            self.iid = str(uuid.uuid4())
        else:
            self.iid = iid

    def __str__(self):
        return "{}/{}/{}".format(self.eid, self.pk, self.iid)

    def get_s3_okey(self):
        return "{}/{}/{}.json".format(self.eid, self.pk, self.iid)

    def get_ddb_hkey(self):
        return self.eid

    def get_ddb_rkey(self):
        return self.iid

    def get_ddb_lsi_rkey(self):
        return self.pk

    @staticmethod
    def from_s3_okey(okey):
        return okey.replace(".json", "").split("/")

    @staticmethod
    def to_s3_okey(eid, pk, iid):
        return "{}/{}/{}.json".format(eid, pk, iid)
