import boto3
import json

class AdptDynamoDB:
    def __init__(self, session, table):
        self.session = session
        self.client = self.session.client("dynamodb")
        self.table = table

    def put(self, item):
        # TODO: need to handle throttling errors
        response = self.client.put_item(
            TableName=self.table,
            Item=item
        )
        return response["ResponseMetadata"]["HTTPStatusCode"]
