import boto3
import json

class AdptS3:
    def __init__(self, session, bucket):
        self.session = session
        self.client = self.session.client("s3")
        self.bucket = bucket

    def put(self, okey, item):
        response = self.client.put_object(
            Bucket=self.bucket,
            Key=okey,
            Body=json.dumps(item)
        )
        return response["ResponseMetadata"]["HTTPStatusCode"]
