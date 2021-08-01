import boto3
import json
from lib.a_ddb import AdptDynamoDB
from lib.a_s3 import AdptS3
from lib.s_counter import SCounter
from lib.s_descriptor import Descriptor

class PortReduce:
    def __init__(self, config):
        self.session = boto3.session.Session()
        self.shuffle_type = config["shuffle_type"]
        if self.shuffle_type == "s3":
            self.shuffle_bucket = config["shuffle_bucket"]
            self.client = AdptS3(self.session, self.shuffle_bucket)
        elif self.shuffle_type == "dynamodb":
            self.shuffle_table = config["shuffle_table"]
            self.shuffle_lsi_all = config["shuffle_lsi_all"]
            self.shuffle_lsi_key = config["shuffle_lsi_key"]
            self.client = AdptDynamoDB(self.session, self.shuffle_table, self.shuffle_lsi_all)
        self.counters_table = config["counters_table"]
        self.counters = SCounter(self.session, self.counters_table)

    def is_ready(self, eid):
        return self.counters.is_ready(eid)

    def list_tier2(self, eid):
        if self.shuffle_type == "s3":
            output = self.client.list_prefixes(eid)
        elif self.shuffle_type == "dynamodb":
            expression_values = {
                ":eid": {"S": eid}
            }
            key_condition = "eid = :eid"
            projection_expression = "eid, pk"

            # local debugging
            # client = self.session.client("dynamodb")
            # response = client.query(
            #     TableName=self.shuffle_table,
            #     IndexName=self.shuffle_lsi_key,
            #     ExpressionAttributeValues=expression_values,
            #     KeyConditionExpression=key_condition,
            #     ProjectionExpression=projection_expression
            # )
            # print(json.dumps(response))
            # items = response["Items"]

            self.client.set_lsi(self.shuffle_lsi_key)
            items = self.client.query(expression_values, key_condition, projection_expression)
            prefixes = set()
            for item in items:
                prefixes.add("{}/{}/".format(item["eid"]["S"], item["pk"]["S"]))
            output = list(prefixes)
        return output

    def list_tier3(self, eid, pk):
        if self.shuffle_type == "s3":
            prefix = "{}/{}".format(eid, pk)
            output = self.client.list_objects(prefix)
        elif self.shuffle_type == "dynamodb":
            expression_values = {
                ":eid": {"S": eid},
                ":pk": {"S": pk}
            }
            key_condition = "eid = :eid AND pk = :pk"
            projection_expression = "eid, pk, iid"
            self.client.set_lsi(self.shuffle_lsi_all)
            items = self.client.query(expression_values, key_condition, projection_expression)
            output = []
            for item in items:
                output.append(Descriptor.to_s3_okey(item["eid"]["S"], item["pk"]["S"], item["iid"]["S"]))
        return output

    def get(self, eid, pk, iid):
        if self.shuffle_type == "s3":
            prefix = Descriptor.to_s3_okey(eid, pk, iid)
            output = json.loads(self.client.get(self.shuffle_bucket, prefix))
        elif self.shuffle_type == "dynamodb":
            hkey = {
                "eid": {"S": eid},
                "iid": {"S": iid}
            }
            output = json.loads(self.client.get(hkey)["data"]["S"])
        return output