import json
import traceback

from lambda_common import (
    dump_context,
    publish_to_analyze_image_sns_topic,
    return_message,
    parse_json,
    Constants,
    HandlerError,
)


def handler(event, context):
    try:
        root_span_id = context.aws_request_id
        print('request: {}'.format(json.dumps(event)))
        print('context: {}'.format(dump_context(context)))

        if 'body' not in event:
            return return_message(400, 'Error: no POST data received')

        body = parse_json(
            event['body'],
            required_fields={
                Constants.IMAGE_URL,
                Constants.POST_ID,
                Constants.ACCOUNT_ID,
                Constants.SOURCE_DEVICE,
                Constants.CREATED_TIMESTAMP,
            },
        )

        sns_response = publish_to_analyze_image_sns_topic(
            body[Constants.IMAGE_URL],
            body[Constants.POST_ID],
            body[Constants.ACCOUNT_ID],
            body[Constants.SOURCE_DEVICE],
            body[Constants.CREATED_TIMESTAMP],
            root_span_id,
        )

        print('SNS Response: {}'.format(sns_response))

        return return_message(
            200,
            f"Successfully accepted for processing: {body} with RootSpanID "
            f"{root_span_id}",
        )
    except HandlerError as e:
        print(f"[ERROR] {e}: ")
        traceback.print_stack()
        return e.create_response()
