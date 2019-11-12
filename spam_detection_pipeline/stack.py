import re

from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_codedeploy as codedeploy,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subscriptions,
    core,
)

# The ARN for the Lambda Layer containing the ImageHash Python library and
# its dependencies.  You can create this by following the instructions in
# the `layers` directory.
IMAGE_HASH_LAYER_ARN = 'arn:aws:lambda:us-east-1:137797084791:layer:ImageHash:1'


def _get_pipeline_lambda_version() -> str:
    """Returns the current version number for the Pipeline Lambdas.

    This is determined by the contents of `lambda/VERSION`.  This is not the same as
    the Lambda version number in AWS.

    :return: The Pipeline Lambda software version number.
    """
    with open('lambda/VERSION') as file:
        return file.read().replace('\n', '').strip()


def _convert_camel_case_to_snake_case(value: str) -> str:
    """Returns a snake case version of the CamelCase string.

    For example, for `ThisIsAnExample`, it returns `this_is_an_example`

    :param value: The CamelCase string
    :return: The snake version of value.
    """
    # Crazy regex to go from CamelCase to snake_case
    # https://stackoverflow.com/questions/1175208/
    #   elegant-python-function-to-convert-camelcase-to-snake-case
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class PipelineLambda:
    """Represents a Lambda that will be created in the SpamDetectionPipeline stack.

    This abstraction has convenience methods for creating and deploying Lambdas
    according to a centralized strategy.
    """

    def __init__(
        self, stack: core.Construct, lambda_app: codedeploy.LambdaApplication, name: str
    ):
        """Creates the underlying Lambda, Lambda Alias, and Deployment Group
        necessary to run this Lambda in the SpamDetectionPipeline stack.

        This code assumes the Lambda's handler can be invoked by the snake
        case verison of the name with `.handler` appended.

        :param stack: The stack.
        :param lambda_app: The Lambda Application that will control the deployments.
        :param name: The camel case name for this Lambda.
        """
        self.__name = name
        # Create the underlying Lambda function on the stack.
        self.__lambda = _lambda.Function(
            stack,
            name,
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler=_convert_camel_case_to_snake_case(name) + '.handler',
        )

        # Create the production alias to use when we want to refer to this Lambda.
        version = self.__lambda.add_version(_get_pipeline_lambda_version())
        self.__lambda_alias = _lambda.Alias(
            stack, name + 'Prod', version=version, alias_name='prod'
        )
        # Create the deployment group that will be used to updated the Lambda
        # based on the alias.
        codedeploy.LambdaDeploymentGroup(
            stack,
            name + 'DN',
            alias=self.__lambda_alias,
            application=lambda_app,
            deployment_config=codedeploy.LambdaDeploymentConfig.ALL_AT_ONCE,
        )

    @property
    def name(self) -> str:
        """
        :return: The name for this Lambda.
        """
        return self.__name

    @property
    def function(self) -> _lambda.Function:
        """
        :return:  The unversioned Lambda Function
        """
        return self.__lambda

    @property
    def alias(self) -> _lambda.Alias:
        """
        :return: The production alias for this Lambda
        """
        return self.__lambda_alias


class SpamDetectionPipelineStack(core.Stack):
    """The SpamDetectionPipeline stack.

    This represents all Lambdas and other resources required to run the
    SpamDetectionPipeline application.
    """

    def __init__(self, scope: core.Construct, stack_id: str, **kwargs) -> None:
        super().__init__(scope, stack_id, **kwargs)

        # A reference to the Layer containing the Image Hash python libaries.
        self.__image_hash_layer = _lambda.LayerVersion.from_layer_version_arn(
            self, stack_id, IMAGE_HASH_LAYER_ARN
        )

        lambda_app = codedeploy.LambdaApplication(
            self,
            'spam-detection-pipeline-lambda-app',
            application_name='SpamDetectionPipelineLambda',
        )

        self.__analyze_image = PipelineLambda(self, lambda_app, 'AnalyzeImage')
        self.__detect_known_bad_content = PipelineLambda(
            self, lambda_app, 'DetectKnownBadContent'
        )
        self.__detect_spammy_words = PipelineLambda(
            self, lambda_app, 'DetectSpammyWords'
        )
        self.__detect_adult_content = PipelineLambda(
            self, lambda_app, 'DetecdtAdultContent'
        )
        self.__update_spam_score = PipelineLambda(self, lambda_app, 'UpdateSpamScore')

        # Only the DetectKnownBadContent needs the ImageHash layer.
        self.__detect_known_bad_content.function.add_layers(self.__image_hash_layer)

        all_lambdas = [
            self.__analyze_image,
            self.__detect_known_bad_content,
            self.__detect_spammy_words,
            self.__detect_adult_content,
            self.__update_spam_score,
        ]

        # Define an API gateway and map the initial and final Lambda
        self.__api = apigw.LambdaRestApi(
            self, 'spam_detection_api', handler=self.__analyze_image.alias, proxy=False
        )
        for pipeline_lambda in all_lambdas:
            self.__map_post_to_lambda_alias(pipeline_lambda)

        # Create an SNS topic to use for fan-out from the initial Lambda
        self.__analyze_requests_topic = sns.Topic(self, "analyze_requests")

        # Add a reference to the SNS Topic ARN to the analyze_image Lambda
        self.__analyze_image.function.add_environment(
            'SNS_ANALYZE_REQUESTS_TOPIC_ARN', self.__analyze_requests_topic.topic_arn
        )

        # Allow the analyze_image lambda to write to the SNS Topic
        self.__analyze_requests_topic.grant_publish(self.__analyze_image.function)

        # For each detection Lambda:
        # - Allow it to invoke the UpdateSpamScore Lambda to report results
        # - Add a subscription to the SNS Topic so it receives processing requests
        for aws_lambda in all_lambdas:
            if aws_lambda.name.startswith('Detect'):
                self.__enable_lambda_to_invoke_update_spam_score(aws_lambda)
                # noinspection PyTypeChecker
                self.__analyze_requests_topic.add_subscription(
                    sns_subscriptions.LambdaSubscription(aws_lambda.alias)
                )

    def __map_post_to_lambda_alias(self, pipeline_lambda: PipelineLambda):
        """Maps POSTs from /{lambda_name} to the prod alias for the specified Lambda.

        Note, {lambda_name} is the snake case version of the Lambda's name.
        """
        resource_name = _convert_camel_case_to_snake_case(pipeline_lambda.name)
        resource = self.__api.root.add_resource(resource_name)
        resource.add_method(
            'POST', integration=apigw.LambdaIntegration(pipeline_lambda.alias)
        )

    def __enable_lambda_to_invoke_update_spam_score(
        self, target_lambda: PipelineLambda
    ):
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
        target_lambda.function.add_environment(
            'LAMBDA_UPDATE_SPAM_SCORE', self.__update_spam_score.alias.function_arn
        )
        self.__update_spam_score.function.grant_invoke(target_lambda.function)
