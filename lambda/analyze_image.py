import traceback

from lambda_common import (
    publish_to_analyze_image_sns_topic,
    return_message,
    parse_json,
    Constants,
    HandlerError,
    LogContext,
)


def handler(event, context):
    root_span_id = context.aws_request_id
    log_context = LogContext(
        'analyze_image',
        context.function_version,
        root_trace=root_span_id,
        parent_trace=root_span_id,
        current_trace=root_span_id,
    )

    try:
        log_context.log_start_message()

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

        log_context.log(
            f"analyzing_image image={body[Constants.IMAGE_URL]} "
            f"account={body[Constants.ACCOUNT_ID]}"
        )

        publish_to_analyze_image_sns_topic(
            body[Constants.IMAGE_URL],
            body[Constants.POST_ID],
            body[Constants.ACCOUNT_ID],
            body[Constants.SOURCE_DEVICE],
            body[Constants.CREATED_TIMESTAMP],
            root_span_id,
            log_context=log_context,
        )

        log_context.log_end_message(200, 'Success')
        return return_message(
            200,
            f"Successfully accepted for processing: {body} with RootSpanID "
            f"{root_span_id}",
        )
    except HandlerError as e:
        print(f"[ERROR] {e}: ")
        traceback.print_stack()
        log_context.log_end_message(e.status_code, f"Failed due to exception: {e}")
        return e.create_response()
