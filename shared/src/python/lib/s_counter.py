import boto3
import botocore
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


    def increment(self, eid, attr, incr=1):
        try:
            response = self.cl_ddb.update_item(
                TableName=self.table,
                Key={
                    "id": {"S": eid}
                },
                ExpressionAttributeNames={
                    "#attr": attr
                },
                ExpressionAttributeValues={
                    ":increment": {"N": str(incr)},
                    ":zero": {"N": "0"}
                },
                UpdateExpression="SET #attr = if_not_exists(#attr, :zero) + :increment",
                ReturnValues="ALL_NEW"
            )
        except botocore.exceptions.ClientError as e:
            response = {
                "error": e
            }
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
