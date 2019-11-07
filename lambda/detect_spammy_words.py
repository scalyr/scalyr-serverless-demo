import json
import boto3
import os
from lambda_common import S3Url, UpdateSpamScoreStub

rekognition_client = boto3.client('rekognition')
update_spam_score = UpdateSpamScoreStub()


def handler(event, context):
    print('event: {}'.format(json.dumps(event)))

    # This is how the Sns payload is nested, it appears only one record is received
    # with each invocation of the Lambda.
    message = json.loads(event['Records'][0]['Sns']['Message'])
    print('message: {}'.format(json.dumps(message)))

    root_trace_id = message['RootTraceID']
    print(f'RootTraceID: {root_trace_id}')

    s3_image = S3Url(message['ImageURL'])

    # Detect text with Rekognition and get a list of dicts with results
    detected_text = get_text_from_image(s3_image.bucket, s3_image.key)
    print('rekognition response: {}'.format(detected_text))

    # Get the confidence threshold to use
    __image_confidence_threshold_value = os.environ.get("IMAGE_CONFIDENCE_THRESHOLD")
    if __image_confidence_threshold_value is None:
        raise MissingSpamScoreThreshold()
    else:
        __image_confidence_threshold = float(__image_confidence_threshold_value)

    # Process the detected text values, if any bad words are found, update the
    # Spam score and stop processing further
    all_words_count = len(detected_text)
    bad_words_count = 0
    for text in detected_text:
        print(
            f'Detected text: {text["DetectedText"]}, '
            f'Confidence: {text["Confidence"]:.2f}%, '
            f'Id: {text["Id"]}, '
            f'Type: {text["Type"]}'
        )
        if text["Confidence"] >= __image_confidence_threshold:
            if is_bad_word(text["DetectedText"]) is True:
                bad_words_count += 1

    score = calculate_score(all_words_count, bad_words_count)

    update_spam_score_result = update_spam_score.invoke(
        {'bucket': s3_image.bucket, 'key': s3_image.key}, 'detect_spammy_words', score
    )
    print(f"update_spam_score_result: {update_spam_score_result}")

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/plain'},
        'body': 'Hello, this is the detect_spammy_words lambda',
    }


def calculate_score(total_words_count: int, bad_words_count: int) -> float:
    """
    Calculate a spam score given the number of words and bad words
    :param total_words_count: int
    :param bad_words_count: int
    :return: float
    """
    score = float(min(bad_words_count, 10) / (min(10, total_words_count)))
    return score


def get_text_from_image(bucket: str, key: str):
    """
    Invokes the AWS Rekognition API with a given bucket and key, and returns a
    a list of dicts with the detection results.
    :param bucket: An AWS S3 bucket name
    :type bucket: str
    :param key: A path to an S3 object, without the bucket name or a leading /
    :type key: str
    :return: list
    """

    response = rekognition_client.detect_text(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}}
    )

    text = response['TextDetections']
    return text


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
