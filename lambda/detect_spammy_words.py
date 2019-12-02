import os

from lambda_common import DetectionHandler, ImagePayload, S3Url, rekognition


class DetectSpammyWordsHandler(DetectionHandler):
    """Spam scoring algorithm meant to see if an image has textual content in
    it that could be spam, based on a list of spammy words.  For example,
    images with "low mortgage rates" will be maked as spam.

    We extract the textual content using the AWS Rekognition service
    and then compare the words with a known spam list.  The higher
    percentage of spammy words in the textual content, the higher
    the spam score.
    """

    def __init__(self):
        super().__init__('detect_spammy_words')

    def _score_image(self, image_payload: ImagePayload) -> float:
        """Score the image based on whether or not it has spammy words.

        :param image_payload:
        :return: The spam score from this algorithm.
        """
        s3_image = S3Url(image_payload.image_url)

        # Detect text with Rekognition and get a list of dicts with results
        detected_text = rekognition(
            self._log_context,
            detect_text={'S3Object': {'Bucket': s3_image.bucket, 'Name': s3_image.key}},
        )

        # Get the confidence threshold to use
        __image_confidence_threshold_value = os.environ.get(
            "IMAGE_CONFIDENCE_THRESHOLD"
        )
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
                if self.__is_bad_word(text["DetectedText"]) is True:
                    bad_words_count += 1

        return self.__calculate_score(all_words_count, bad_words_count)

    @staticmethod
    def __calculate_score(total_words_count: int, bad_words_count: int) -> float:
        """
        Calculate a spam score given the number of words and bad words
        :param total_words_count: int
        :param bad_words_count: int
        :return: float
        """
        return float(min(bad_words_count, 10) / (min(10, total_words_count))) * 100

    @staticmethod
    def __is_bad_word(word: str) -> bool:
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


def handler(event, context):
    return DetectSpammyWordsHandler().handle_request(event, context)


class MissingSpamScoreThreshold(Exception):
    """
    Raised if the environment variable containing the Spam Score Threshold is missing.
    """

    pass
