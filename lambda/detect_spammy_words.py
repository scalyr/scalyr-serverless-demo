import json
import boto3
from lambda_common import S3Url

client = boto3.client('rekognition')


def handler(event, context):
    print('request: {}'.format(json.dumps(event)))

    message = json.loads(event['Records'][0]['Sns']['Message'])

    print('message: {}'.format(json.dumps(message)))

    s3_image = S3Url(message['ImageURL'])

    print('bucket: {}, key: {}'.format(s3_image.bucket, s3_image.key))

    rekognition_response = detect_text(s3_image.bucket, s3_image.key)
    print('rekognition response: {}'.format(rekognition_response))

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/plain'},
        'body': 'Hello, this is the detect_spammy_words lambda',
    }


def detect_text(bucket, image):
    response = client.detect_text(Image={'S3Object': {'Bucket': bucket, 'Name': image}})

    text_detections = response['TextDetections']
    print('Detected text\n----------')
    for text in text_detections:
        print(
            'Detected text: {}, Confidence: {:.2f}%, Id: {}, Type: {}'.format(
                text['DetectedText'], text['Confidence'], text['Id'], text['Type']
            )
        )
        if 'ParentId' in text:
            print('Parent Id: {}'.format(text['ParentId']))
    return text_detections
