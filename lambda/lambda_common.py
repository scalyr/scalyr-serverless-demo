import boto3
import os
import json
from urllib.parse import urlparse


class UpdateSpamScoreStub(object):
    """
    Helper class that can be used to invoke the `UpdateSpamScore` Lambda from
    other Lambdas.  It is a small wrapper around the main AWS SDK Lambda invoke
    mechanisms.  It handles accepting the normal arguments, verifying the
    result, and parsing the response.

    NOTE: This relies on a `LAMBDA_UPDATE_SPAM_SCORE` environment variable
    containing the ARN of the `UpdateSpamScore` Lambda to use.
    """

    def __init__(self):
        """
        Initializes an instance that can be used to invoked the UpdateSpamScore Lambda.
        """
        self.__lambda_arn = os.environ.get('LAMBDA_UPDATE_SPAM_SCORE', default=None)
        if self.__lambda_arn is None:
            raise MissingLambdaArn()
        self.__lambda_client = boto3.client('lambda')

    def invoke(self, payload, algorithm, score):
        """
        Invokes the UpdateSpamScore Lambda, blocks for a response, and returns
        the result.

        If this calls is unsuccessful, a `UpdateSpamScoreFailure` exception
        will be raised.

        :param payload: The image payload whose spam score is being updated.
        :type payload: dict
        :param algorithm: The name of the algorithm reporting its score
        :type algorithm: str
        :param score: The spam score that this algorithm gave to the image.
        :type score: Number

        :return: The response body if the request is successful.
        :rtype: str
        """
        args = {"image_payload": payload, "score": score, "algorithm": algorithm}

        response = self.__lambda_client.invoke(
            FunctionName=self.__lambda_arn,
            InvocationType='RequestResponse',
            Payload=json.dumps(args),
        )
        if response['StatusCode'] != 200:
            raise UpdateSpamScoreFailure(response['StatusCode'])

        return json.loads(response['Payload'].read())['body']


class MissingLambdaArn(Exception):
    """
    Raised if the environment variable containing the Lambda is missing.
    """

    pass


class UpdateSpamScoreFailure(Exception):
    """
    Raised if an invocations of the UpdateSpamScore Lambda fails.
    """

    def __init__(self, status_code):
        """
        Creates an instance.

        :param status_code: The http status code
        :type status_code: Number
        """
        self.__status_code = status_code

    @property
    def status_code(self):
        return self.__status_code


class ImagePayload:
    def __init__(
        self,
        image_url: str,
        post_id: str,
        account_id: str,
        source_device: str,
        created_timestamp: float,
    ):
        """
        Holds data about an Image Payload, and can serialize the data with .to_json()

        :param image_url: A S3 URL to an image in a publicly accessible bucket
        :type image_url: str
        :param post_id: A unique ID for the post
        :type post_id: str
        :param account_id: A unique ID for the account creating the post
        :type account_id: str
        :param source_device: The device type like ios, android, web, etc
        :type source_device: str
        :param created_timestamp: A unix timestamp when the post was created
        :type created_timestamp: float

        :return: A JSON payload for processing by the Lambdas
        :rtype: str
        """
        self.image_url = image_url
        self.post_id = post_id
        self.account_id = account_id
        self.source_device = source_device
        self.created_timestamp = created_timestamp

    def to_json(self) -> str:
        payload = {
            'ImageURL': self.image_url,
            'PostID': self.post_id,
            'AccountID': self.account_id,
            'SourceDevice': self.source_device,
            'CreatedTimestamp': self.created_timestamp,
        }

        return json.dumps(payload)


class S3Url(object):
    """
    Helper class that takes a S3 URL in format "S3://bucket/path/file.jpeg"
    and has methods to retrieve the Bucket name, Key name, and entire URL
    """

    def __init__(self, url):
        try:
            self._parsed = urlparse(url, allow_fragments=False)

            self._bucket = self._parsed.netloc
            self._key = self._parsed.path.lstrip('/')
            self._url = self._parsed.geturl()
        except ValueError:
            print("exception while attempting to urlparse: {}".format(url))
            raise

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def key(self) -> str:
        return self._key

    @property
    def url(self) -> str:
        return self._url
