import json


def handler(event, context):
    print('request: {}'.format(json.dumps(event)))

    message = json.loads(event['Records'][0]['Sns']['Message'])
    print('message: {}'.format(json.dumps(message)))

    root_trace_id = message['RootTraceID']
    print(f'RootTraceID: {root_trace_id}')

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/plain'},
        'body': 'Hello, Detect Known Bad Content Friend, you have reached {}\n'.format(
            event['path']
        ),
    }
