import boto3
import imagehash
import io

from PIL import Image


from lambda_common import DetectionHandler, ImagePayload, S3Url

_s3 = boto3.client('s3')

# The different between the perceptual image hashes and the confidence that
# they are the same image.
# TODO: We should probably make this configurable using environment variables.
MAX_HASH_OFFSET = 100000
CONFIDENCE_10_PERCENT_HASH_OFFSET = MAX_HASH_OFFSET
CONFIDENCE_50_PERCENT_HASH_OFFSET = MAX_HASH_OFFSET / 10
CONFIDENCE_90_PERCENT_HASH_OFFSET = CONFIDENCE_50_PERCENT_HASH_OFFSET / 10
CONFIDENCE_95_PERCENT_HASH_OFFSET = CONFIDENCE_90_PERCENT_HASH_OFFSET / 10


class DetectKnownBadContentHandler(DetectionHandler):
    """Spam scoring algorithm meant to see if a given image is the same as
    any image in a database of known bad images.  We use a perceptual-based
    image hashing algorithm so that we can detect similar images even if they
    have been resized, compressed at a lower quality, etc.

    The spam score is computed based on how similar the image is to the
    image from the bad images database.  The more similar, the higher the
    score.
    """

    def __init__(self):
        super().__init__('detect_known_bad_content')

    def _score_image(self, image_payload: ImagePayload) -> float:
        """Score the image based on the known bad content.

        :param image_payload:
        :return: The spam score from this algorithm.
        """
        # Fetch image from S3
        # Emit about start/end of image fetch
        s3_image = S3Url(image_payload.image_url)
        obj = _s3.get_object(Bucket=s3_image.bucket, Key=s3_image.key)
        image_content = Image.open(io.BytesIO(obj['Body'].read()))

        # Use the perceptual hash algorithm.  Note, imagehash has many
        # different perceptual hashes, so we could experiment to find
        # which work best for this application.
        ahash = imagehash.average_hash(image_content)

        closest_hash, image_id = self.__find_closest_image(ahash)
        # Emit about hash and closest image

        if closest_hash is not None:
            hash_diff = abs(closest_hash - ahash)
            if hash_diff >= CONFIDENCE_95_PERCENT_HASH_OFFSET:
                return 0.95
            elif hash_diff >= CONFIDENCE_90_PERCENT_HASH_OFFSET:
                return 0.90
            elif hash_diff >= CONFIDENCE_50_PERCENT_HASH_OFFSET:
                return 0.50
            elif hash_diff >= CONFIDENCE_10_PERCENT_HASH_OFFSET:
                return 0
            else:
                return 0
        else:
            return 0

    @staticmethod
    def __find_closest_image(_target_hash: int):
        """Find the most similar known bad image to the target image.

        This will only return a match if there is a similar image within
        `MAX_HASH_OFFSET` to the target image.

        :param _target_hash: The perceptual hash of the target image
        :return: If a similar image is found, this returns a tuple of
            perceptual hash for the image and its id.  Otherwise None, None
            is returned.
        :rtype: (int, str)
        """
        # Simulation fake:  We won't bother to really track a database of
        # known bad content. To implement this for real, we would need to
        # do a database lookup for a hash that is within MAX_HASH_DIFFERENCE
        # of the target hash.  This should be pretty easy for a scanning
        # database.
        return None, None


def handler(event, context):
    return DetectKnownBadContentHandler().handle_request(event, context)
