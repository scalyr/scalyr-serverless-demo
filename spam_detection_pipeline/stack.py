from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    aws_iam as _iam,
    core,
)


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

        self.__worker_lambdas = {
            'detect_known_bad_content': self.__detect_known_bad_content_lambda,
            'detect_spammy_words': self.__detect_spammy_words_lambda,
            'detect_adult_content': self.__detect_adult_content_lambda,
        }

        # Define an API gateway and map the initial and final Lambda
        self.__api = apigw.LambdaRestApi(
            self, 'spam_detection_api', handler=self.__analyze_image_lambda, proxy=False
        )
        self.__map_post_to_lambda('analyze_image', self.__analyze_image_lambda)
        self.__map_post_to_lambda('update_spam_score', self.__update_spam_score_lambda)

        # Create an SNS topic to use for fan-out from the initial Lambda
        self.__analyze_requests_topic = sns.Topic(self, "analyze_requests")

        # Add a reference to the SNS Topic ARN to the analyze_image Lambda
        self.__analyze_image_lambda.add_environment(
            'SNS_ANALYZE_REQUESTS_TOPIC_ARN', self.__analyze_requests_topic.topic_arn
        )

        # Allow the analyze_image lambda to write to the SNS Topic
        self.__analyze_requests_topic.grant_publish(self.__analyze_image_lambda)

        # For each worker Lambda:
        # - Allow it to invoke the UpdateSpamScore Lambda to report results
        # - Add a subscription to the SNS Topic so it receives processing requests
        # - Allow it to invoke AWS Rekognition via AWS Managed IAM Policy
        # - Add a PolicyStatement for access to the S3 bucket
        # - Add a API gateway mapping for debugging
        for name, aws_lambda in self.__worker_lambdas.items():
            self.__enable_lambda_to_invoke_update_spam_score(aws_lambda)
            self.__analyze_requests_topic.add_subscription(
                sns_subscriptions.LambdaSubscription(aws_lambda)
            )
            aws_lambda.role.add_managed_policy(
                _iam.ManagedPolicy.from_aws_managed_policy_name(
                    'AmazonRekognitionFullAccess'
                )
            )
            aws_lambda.role.add_to_policy(
                _iam.PolicyStatement(
                    actions=['*'], resources=['arn:aws:s3:::scalyr-serverless-demo/*']
                )
            )

            self.__map_post_to_lambda(name, aws_lambda)

    def __create_lambda(self, name, handler) -> _lambda.Function:
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
