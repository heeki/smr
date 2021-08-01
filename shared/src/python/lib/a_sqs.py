import boto3
import botocore

class AdptSQS:
    def __init__(self, session, queue):
        self.session = session
        self.client = self.session.client("sqs")
        self.queue = queue

    def send_message_batch(self, batches):
        try:
            response = self.client.send_message_batch(
                QueueUrl=self.queue,
                Entries=batches
            )
        except botocore.exceptions.ClientError as e:
            print(e)
            half = len(batches)//2
            a = batches[:half]
            b = batches[half:]
            response = []
            if len(a) > 0:
                response.append(self.client.send_message_batch(
                    QueueUrl=self.queue,
                    Entries=a
                ))
            if len(b) > 0:
                response.append(self.client.send_message_batch(
                    QueueUrl=self.queue,
                    Entries=b
                ))
        return response
