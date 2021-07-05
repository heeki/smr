import boto3
import decimal
import json

# helper class
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return json.JSONEncoder.default(self, o)

class SCounter:
    def __init__(self, table):
        self.session = boto3.session.Session()
        self.cl_ddb = self.session.client("dynamodb")
        self.table = table

    def increment(self, eid, attr):
        response = self.cl_ddb.update_item(
            TableName=self.table,
            Key={
                "id": {"S": eid}
            },
            ExpressionAttributeValues={
                ":increment": { "N": "1" }
            },
            UpdateExpression="SET {} = {} + :increment".format(attr, attr),
            ReturnValues="UPDATED_NEW"
        )
        return response

    def get(self, eid, attr):
        item = self.cl_ddb.get_item(
            TableName=self.table,
            Key={
                "id": {"S": eid}
            }
        )["Item"]
        if attr in item:
            return int(item[attr]["N"])
        else:
            return -1

    def check_ready(self, eid):
        item = self.cl_ddb.get_item(
            TableName=self.table,
            Key={
                "id": {"S": eid}
            }
        )["Item"]
        if "ingested" in item and "mapped" in item and int(item["ingested"]["N"]) == int(item["mapped"]["N"]):
            return True
        else:
            return False
