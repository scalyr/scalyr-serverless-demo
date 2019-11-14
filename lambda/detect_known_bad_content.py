from lambda_common import DetectionHandler, ImagePayload


class DetectKnownBadContentHandler(DetectionHandler):
    def __init__(self):
        super().__init__('detect_known_bad_content')

    def _score_image(self, _image_payload: ImagePayload) -> float:
        return 0.0


def handler(event, context):
    return DetectKnownBadContentHandler().handle_request(event, context)
