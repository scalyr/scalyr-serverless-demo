import traceback

from lambda_common import (
    receive_from_update_spam_score_sns_topic,
    HandlerError,
    return_message,
    LogContext,
    InvalidHandlerInputError,
)


def get_current_scores(_image_url: str, _account_id: str) -> dict:
    """Retrieves the current spam scores for the specified image.

    :param _image_url: The image URL.
    :param _account_id: The account id.
    :return: The spam scores in a dict, an entry for each algorithm.
    """
    # Simulation cheat:  We aren't really bothering to store the
    # spam scores
    return {}


def update_score(scorer: str, score: float, image_url: str, account_id: str) -> bool:
    """Simulates updating the spam score for the specified image.
    :param scorer:  The name of the scoring algorithm that computed the score.
    :param score: The score
    :param image_url: The image URL.
    :param account_id: The account id posting the image.
    """
    if score < 0 or score > 1:
        raise InvalidHandlerInputError(f"Invalid score: score={score}")

    current_scores = get_current_scores(image_url, account_id)

    current_scores[scorer] = score

    max_score = max(current_scores.values())
    average_score = sum(current_scores.values()) / len(current_scores)

    is_spam = max_score > 0.75 or (average_score > 0.5 and len(current_scores) == 3)
    # Simulation fake:  We should write the score here.
    return is_spam


def handler(event, context):
    log_context = None
    scorer = None

    try:
        update_spam_score_payload = receive_from_update_spam_score_sns_topic(event)
        scorer = update_spam_score_payload.scorer

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

        is_spam = update_score(
            update_spam_score_payload.scorer,
            update_spam_score_payload.score,
            update_spam_score_payload.image_payload.image_url,
            update_spam_score_payload.image_payload.account_id,
        )

        log_context.log(f"spam_result is_spam={is_spam}")

        log_context.log_end_message(200, "Success")
        return return_message(200, f"Event: {event}")
    except HandlerError as e:
        print(f"[ERROR] Error while processing request from {scorer}: {e}:")
        traceback.print_exc()
        if log_context is not None:
            log_context.log_end_message(e.status_code, f"Failed due to exception: {e}")
        return e.create_response(for_sns_topic=True)
