import unittest
import json

from lambda_common import S3Url, ImagePayload


class TestS3URL(unittest.TestCase):
    def setUp(self):
        self.s3_url = S3Url("s3://bucket/path/file.jpeg")

    def test_parse_s3_url(self):
        assert self.s3_url.bucket == "bucket"
        assert self.s3_url.key == "path/file.jpeg"
        assert self.s3_url.url == "s3://bucket/path/file.jpeg"


class TestImagePayload(unittest.TestCase):
    def setUp(self):
        self.image_payload = ImagePayload(
            "s3://scalyr-serverless-demo/green.png",
            "xyz123",
            "789",
            "iOS",
            "1572457843",
            "Root=1-5dc424fe-34aaedd01ccd08b4a54a3bd8",
        )

    def test_image_payload_tojson(self):
        __json = {
            "ImageURL": "s3://scalyr-serverless-demo/green.png",
            "PostID": "xyz123",
            "AccountID": "789",
            "SourceDevice": "iOS",
            "CreatedTimestamp": "1572457843",
            "RootTraceID": "Root=1-5dc424fe-34aaedd01ccd08b4a54a3bd8",
        }
        assert json.loads(self.image_payload.to_json()) == __json
