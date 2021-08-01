import boto3
import botocore

class AdptDynamoDB:
    def __init__(self, session, table, lsi=None):
        self.session = session
        self.client = self.session.client("dynamodb")
        self.table = table
        self.lsi = lsi

    def get(self, hkey):
        response = self.client.get_item(
            TableName=self.table,
            Key=hkey
        )
        if "Item" in response:
            return response["Item"]
        else:
            return {}

    def put(self, item):
        # TODO: need to handle throttling errors
        try:
            response = self.client.put_item(
                TableName=self.table,
                Item=item
            )
        except botocore.exceptions.ResourceNotFoundException as e:
            response = {
                "ResponseMetadata": {
                    "HTTPStatusCode": 404
                },
                "error": e
            }
        return response["ResponseMetadata"]["HTTPStatusCode"]

    def increment(self, hkey, attr, incr=1):
        try:
            response = self.client.update_item(
                TableName=self.table,
                Key=hkey,
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

    def query(self, expression_values, key_condition, projection_expression):
        response = self.client.query(
            TableName=self.table,
            IndexName=self.lsi,
            ExpressionAttributeValues=expression_values,
            KeyConditionExpression=key_condition,
            ProjectionExpression=projection_expression
        )
        if "Items" in response:
            return response["Items"]
        else:
            return []
