import traceback

from lambda_common import (
    receive_from_update_spam_score_sns_topic,
    HandlerError,
    return_message,
    LogContext,
)


def handler(event, context):
    log_context = None

    try:
        update_spam_score_payload = receive_from_update_spam_score_sns_topic(event)

        log_context = LogContext(
            'update_spam_score',
            context.function_version,
            root_trace=update_spam_score_payload.image_payload.root_trace_id,
            parent_trace=update_spam_score_payload.scorer_trace_id,
            current_trace=context.aws_request_id,
        )

        log_context.log_start_message()

        log_context.log(
            f"update_spam_score algorithm={update_spam_score_payload.scorer} "
            f"score={update_spam_score_payload.score} "
            f"image={update_spam_score_payload.image_payload.image_url}"
        )

        log_context.log_end_message(200, "Success")
        return return_message(200, f"Event: {event}")
    except HandlerError as e:
        print(f"[ERROR] {e}: ")
        traceback.print_stack()
        if log_context is not None:
            log_context.log_end_message(e.status_code, f"Failed due to exception: {e}")
        return e.create_response()
