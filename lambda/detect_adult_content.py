from lambda_common import DetectionHandler, ImagePayload, S3Url, rekognition


class DetectAdultContentHandler(DetectionHandler):
    """Spam scoring algorithm meant to see if a given image has adult content.

    We detect adult content using the AWS Rekognition service.

    We compute the spam score based on the confidence score of the highest
    confidence moderation label from Rekognition.
    """

    def __init__(self):
        super().__init__('detect_adult_content')

    def _score_image(self, image_payload: ImagePayload) -> float:
        """Score the image based on whether or not it has adult content.

        :param image_payload:
        :return: The spam score from this algorithm.
        """
        s3_image = S3Url(image_payload.image_url)

        # Use Rekognition to detect adult-orientation moderation labels.
        labels = rekognition(
            self._log_context,
            detect_moderation_labels={
                'S3Object': {'Bucket': s3_image.bucket, 'Name': s3_image.key}
            },
        )

        score = 0.0
        # We assign the score based on the highest confidence moderation label.
        for label in labels:
            # The Confidence is measured from 0 to 100.
            if label["Name"] == "Explicit Nudity" or label["Name"] == "Suggestive":
                score = max(score, label["Confidence"] / 100)

        return score


def handler(event, context):
    return DetectAdultContentHandler().handle_request(event, context)
