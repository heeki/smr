import boto3
import json

class AdptSFn:
    def __init__(self, session, account_id):
        self.session = session
        self.client = self.session.client("stepfunctions")
        self.account_id = account_id

    def describe_execution(self, sfn_name, eid):
        arn = "arn:aws:states:us-east-1:{}:execution:{}:{}".format(self.account_id, sfn_name, eid)
        # response = self.client.describe_state_machine_for_execution(
        response = self.client.describe_execution(
            executionArn=arn,
        )
        return response

    def _get_execution_history(self, arn, next_token=None):
        if next_token is None:
            response = self.client.get_execution_history(
                executionArn=arn
            )
        else:
            response = self.client.get_execution_history(
                executionArn=arn,
                nextToken=next_token
            )
        return response

    def get_execution_history(self, sfn_name, eid):
        output = []
        arn = "arn:aws:states:us-east-1:{}:execution:{}:{}".format(self.account_id, sfn_name, eid)
        response = self._get_execution_history(arn)
        output.extend(response["events"])
        while "nextToken" in response:
            response = self._get_execution_history(arn, response["nextToken"])
            output.extend(response["events"])
        return output

    def invoke(self, sfn_name, payload):
        arn = "arn:aws:states:us-east-1:{}:stateMachine:{}".format(self.account_id, sfn_name)
        response = self.client.start_execution(
            stateMachineArn=arn,
            input=json.dumps(payload)
        )
        return response
