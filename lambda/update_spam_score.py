import json
import traceback
from lambda_common import (
    dump_context,
    receive_from_update_spam_score_sns_topic,
    HandlerError,
    return_message,
)


def handler(event, context):
    try:
        print('request: {}'.format(json.dumps(event)))
        print('context: {}'.format(dump_context(context)))

        update_spam_score_payload = receive_from_update_spam_score_sns_topic(event)

        print(
            'Received score of {} from {}'.format(
                update_spam_score_payload.scorer, update_spam_score_payload.score
            )
        )
        return return_message(200, f"Event: {event}")
    except HandlerError as e:
        print(f"[ERROR] {e}: ")
        traceback.print_stack()
        return e.create_response()
