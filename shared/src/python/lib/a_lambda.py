import boto3
import json

class AdptLambda:
    def __init__(self, session):
        self.session = session
        self.client = self.session.client("lambda")

    def invoke(self, fn, payload, invoke_type="RequestResponse"):
        response = self.client.invoke(
            FunctionName=fn,
            InvocationType=invoke_type,
            LogType="None",
            Payload=json.dumps(payload)
        )
        return response
