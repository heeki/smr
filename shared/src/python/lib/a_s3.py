import boto3

class AdptS3:
    def __init__(self, session, bucket):
        self.session = session
        self.client = self.session.client("s3")
        self.bucket = bucket

    def get(self, bucket, key):
        response = self.client.get_object(
            Bucket=bucket,
            Key=key
        )
        # TODO: convert from reading entire file to handle streaming body
        try:
            output = response["Body"].read().decode("utf-8")
        except Exception as e:
            output = response["Body"].read().decode("latin-1")
        return output

    def put(self, okey, item):
        response = self.client.put_object(
            Bucket=self.bucket,
            Key=okey,
            Body=item
        )
        return response["ResponseMetadata"]["HTTPStatusCode"]

    def list_objects(self, prefix):
        paginator = self.client.get_paginator("list_objects_v2")
        pages = paginator.paginate(
            Bucket=self.bucket,
            Prefix=prefix
        )
        output = []
        for page in pages:
            for content in page["Contents"]:
                output.append(content["Key"])
        return output

    def list_prefixes(self, eid):
        response = self.client.list_objects(
            Bucket=self.bucket,
            Prefix="{}/".format(eid),
            Delimiter="/"
        )
        output = []
        if "CommonPrefixes" in response:
            for prefix in response["CommonPrefixes"]:
                output.append(prefix["Prefix"])
        return output
