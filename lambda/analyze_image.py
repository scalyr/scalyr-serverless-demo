import json
import os
import boto3
from lambda_common import ImagePayload

_sns = boto3.client('sns')
SNS_ARN = os.environ['SNS_ANALYZE_REQUESTS_TOPIC_ARN']


def handler(event, context):
    print('request: {}'.format(json.dumps(event)))

    if 'body' not in event:
        return return_message(400, "Error: no POST data received")

    body = json.loads(event['body'])

    if not set(
        ('ImageURL', 'PostID', 'AccountID', 'SourceDevice', 'CreatedTimestamp')
    ).issubset(body):
        return return_message(400, "Error: Invalid message body")

    payload = ImagePayload(
        body['ImageURL'],
        body['PostID'],
        body['AccountID'],
        body['SourceDevice'],
        body['CreatedTimestamp'],
    )

    # TODO(Brian): Validate body and only send desired fields to SNS
    sns_response = _sns.publish(TopicArn=SNS_ARN, Message=payload.to_json())
    print('SNS Response: {}'.format(sns_response))

    return return_message(200, "Successfully accepted for processing: {}".format(body))


def return_message(code, message):
    return {
        'statusCode': code,
        'headers': {'Content-Type': 'text/plain'},
        'body': message,
    }
