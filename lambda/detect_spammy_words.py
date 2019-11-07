import json
import boto3
import os
from lambda_common import S3Url, UpdateSpamScoreStub

rekognition_client = boto3.client('rekognition')


def handler(event, context):
    print('event: {}'.format(json.dumps(event)))

    # This is how the Sns payload is nested, it appears only one record is received
    # with each invocation of the Lambda.
    message = json.loads(event['Records'][0]['Sns']['Message'])

    print('message: {}'.format(json.dumps(message)))

    s3_image = S3Url(message['ImageURL'])

    print('bucket: {}, key: {}'.format(s3_image.bucket, s3_image.key))

    rekognition_response = process_text(s3_image.bucket, s3_image.key)
    print('rekognition response: {}'.format(rekognition_response))

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/plain'},
        'body': 'Hello, this is the detect_spammy_words lambda',
    }


def process_text(bucket: str, key: str):
    """
    Invokes the AWS Rekognition API with a given bucket and key, and returns a
    spam score from 0 to 1, 1 being most likely to be spam.
    :param bucket: An AWS S3 bucket name
    :type bucket: str
    :param key: A path to an S3 object, without the bucket name or a leading /
    :type key: str
    :return:
    """
    # TODO: It may make sense to have an additional abstraction between
    # detecting the text and calculating the spam_score. Putting it all in here for now.

    # TODO: Temporary hack to make MyPy stop complaining about incompatible types
    __image_confidence_threshold_value = os.environ.get("IMAGE_CONFIDENCE_THRESHOLD")
    if __image_confidence_threshold_value is None:
        raise MissingSpamScoreThreshold()
    else:
        __image_confidence_threshold = float(__image_confidence_threshold_value)

    update_spam_score = UpdateSpamScoreStub()

    response = rekognition_client.detect_text(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}}
    )

    text_detections = response['TextDetections']
    for text in text_detections:
        print(
            f'Detected text: {text["DetectedText"]}, '
            f'Confidence: {text["Confidence"]:.2f}%, '
            f'Id: {text["Id"]}, '
            f'Type: {text["Type"]}'
        )
        if text["Confidence"] >= __image_confidence_threshold:
            if is_bad_word(text["DetectedText"]) is True:
                update_spam_score_result = update_spam_score.invoke(
                    {'bucket': bucket, 'key': key}, 'detect_spammy_words', 1
                )
                print(f'update_spam_score_result: {update_spam_score_result}')


def is_bad_word(word: str) -> bool:
    """
    Returns true if the given word is in a bad words list
    :param word:
    :type word: str
    :return: bool
    """
    bad_words = ["red", "green", "blue", "yellow", "purple", "orange"]

    if word in bad_words:
        return True
    else:
        return False


class MissingSpamScoreThreshold(Exception):
    """
    Raised if the environment variable containing the Spam Score Threshold is missing.
    """

    pass
