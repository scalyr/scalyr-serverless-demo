from aws_cdk import aws_lambda as _lambda, aws_apigateway as apigw, core


class SpamDetectionPipelineStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # Create references to all of the Lambdas.
        self.__analyze_image_lambda = self.__create_lambda(
            'AnalyzeImage', 'analyze_image.handler'
        )
        self.__detect_adult_content_lambda = self.__create_lambda(
            'DetectAdultContent', 'detect_adult_content.handler'
        )
        self.__detect_spammy_words_lambda = self.__create_lambda(
            'DetectSpammyWords', 'detect_spammy_words.handler'
        )
        self.__detect_known_bad_content_lambda = self.__create_lambda(
            'DetectKnownBadContent', 'detect_known_bad_content.handler'
        )
        self.__update_spam_score_lambda = self.__create_lambda(
            'UpdateSpamScore', 'update_spam_score.handler'
        )

        # Enable the detection algorithms to invoke the UpdateSpamScore Lambda
        # to report their results
        self.__enable_lambda_to_invoke_update_spam_score(
            self.__detect_known_bad_content_lambda
        )
        self.__enable_lambda_to_invoke_update_spam_score(
            self.__detect_spammy_words_lambda
        )
        self.__enable_lambda_to_invoke_update_spam_score(
            self.__detect_adult_content_lambda
        )

        # Now define a gateway that maps paths to those Lambdas.
        self.__api = apigw.LambdaRestApi(
            self, 'spam_detection_api', handler=self.__analyze_image_lambda, proxy=False
        )
        self.__map_post_to_lambda('analyze_image', self.__analyze_image_lambda)
        self.__map_post_to_lambda(
            'detect_adult_content', self.__detect_adult_content_lambda
        )
        self.__map_post_to_lambda(
            'detect_spammy_words', self.__detect_spammy_words_lambda
        )
        self.__map_post_to_lambda(
            'detect_known_bad_content', self.__detect_known_bad_content_lambda
        )
        self.__map_post_to_lambda('update_spam_score', self.__update_spam_score_lambda)

    def __create_lambda(self, name, handler):
        """
        :param name: The name of the Lambda
        :type name: str
        :param handler: The name handler in its module, specified as a string
            relative to the lambda package.
        :type handler: str
        :return: The Lambda object
        :rtype: Lambda
        """
        return _lambda.Function(
            self,
            name,
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler=handler,
        )

    def __map_post_to_lambda(self, resource_name, lambda_function):
        """Maps POSTs to /{resource_name} to the specified Lambda function.

        :param resource_name: The name of the resource
        :type resource_name: str
        :param lambda_function: The Lambda function
        :type lambda_function: Lambda
        """
        resource = self.__api.root.add_resource(resource_name)
        resource.add_method(
            'POST', integration=apigw.LambdaIntegration(lambda_function)
        )

    def __enable_lambda_to_invoke_update_spam_score(self, target_lambda):
        """
        Configures `target_lambda` to be able to invoke the
        `UpdateSpamScore` Lambda.

        This is accomplished by both granting the Lambda permission to invoke
        `UpdateSpamScore` and to add information to its environment so that it
        can locate `UpdateSpamScore`.

        :param target_lambda: The target Lambda.
        :type target_lambda: Lambda
        """
        # Publish the Lambda's ARN into the environment so it can be used to
        # connect to the right Lambda.
        #
        # Note, this environment variable must be the same as used in
        # `lambda_common.py`.
        target_lambda.add_environment(
            'LAMBDA_UPDATE_SPAM_SCORE', self.__update_spam_score_lambda.function_arn
        )
        self.__update_spam_score_lambda.grant_invoke(target_lambda)
