from aws_cdk import aws_lambda as _lambda, aws_apigateway as apigw, core


class SpamDetectionPipelineStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        analyze_image_lambda = _lambda.Function(
            self,
            'AnalyzeImage',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='analyze_image.handler',
        )

        detect_adult_content_lambda = _lambda.Function(
            self,
            'DetectAdultContent',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='detect_adult_content.handler',
        )

        detect_spammy_words_lambda = _lambda.Function(
            self,
            'DetectSpammyWords',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='detect_spammy_words.handler',
        )

        detect_known_bad_content_lambda = _lambda.Function(
            self,
            'DetectKnownBadContent',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='detect_known_bad_content.handler',
        )

        update_spam_score_lambda = _lambda.Function(
            self,
            'UpdateSpamScore',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='update_spam_score.handler',
        )

        apigw.LambdaRestApi(self, 'Endpoint', handler=analyze_image_lambda)
        apigw.LambdaRestApi(self, 'Endpoint', handler=detect_adult_content_lambda)
        apigw.LambdaRestApi(self, 'Endpoint', handler=detect_spammy_words_lambda)
        apigw.LambdaRestApi(self, 'Endpoint', handler=detect_known_bad_content_lambda)
        apigw.LambdaRestApi(self, 'Endpoint', handler=update_spam_score_lambda)
