import json


def handler(event, context):
    print('request: {}'.format(json.dumps(event)))
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/plain'},
        'body': 'Hello, Detect Known Bad Content Friend, you have reached {}\n'.format(
            event['path']
        ),
    }
