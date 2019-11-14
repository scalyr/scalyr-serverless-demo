from lambda_common import DetectionHandler, ImagePayload


class DetectAdultContentHandler(DetectionHandler):
    def __init__(self):
        super().__init__('detect_adult_content')

    def _score_image(self, image_payload: ImagePayload) -> float:
        return 0.0


def handler(event, context):
    return DetectAdultContentHandler().handle_request(event, context)
