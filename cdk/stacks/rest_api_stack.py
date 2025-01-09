from dataclasses import dataclass, field
from typing import Optional, Dict

from aws_cdk import (
    aws_iam as iam,
    aws_kms as kms,
    aws_secretsmanager as sm,
    aws_lambda,
    Duration,
    RemovalPolicy,
    aws_ecr as ecr,
    CfnOutput,
    Aws,
)
from constructs import Construct

from cdk.stacks.base_stack import BaseStack


@dataclass
class RestApiStackProps:
    """
    Represents the properties required to define an API stack.

    Attributes:
        api_handler_name (str): The name of the API handler.
        environment_variables (dict): A dictionary of environment variables.
        repo_name (str): The name of the repository associated with the API.
        removal_policy (RemovalPolicy): The policy that defines what happens to the stack when removed.
    """
    api_handler_name: str
    repo_name: str
    removal_policy: RemovalPolicy
    environment_variables: Optional[Dict[str, str]] = field(default_factory=dict)


class RestApiStack(BaseStack):
    """
    Class for creating a RestApiStack which includes necessary resources like Lambda Function, KMS Key, API Key, and IAM Role.

    Attributes:
        api_handler (aws_lambda.Function): The Lambda function handler for API requests.
        api_key (sm.Secret): The API key stored securely in Secrets Manager.
        handler_role (iam.Role): The IAM role for Lambda function execution.
        kms_key (kms.Key): The KMS key used for encryption.

    Methods:
        __init__(scope, construct_id, props, **kwargs):
            Initializes the RestApiStack with required AWS resources and configuration.

        __create_kms_cmk():
            Creates an AWS KMS Customer Master Key (CMK) for encryption.

        __create_api_key(kms_cmk):
            Creates an API key and stores it securely using AWS Secrets Manager, encrypted with the provided KMS CMK.

        __create_handler_role(removal_policy):
            Creates the IAM role for the Lambda function execution with necessary permissions.

        __create_api_handler(code, environment_variables, function_name):
            Creates the Lambda function handler with the specified code, environment variables, and function name.
    """
    api_handler: aws_lambda.Function
    api_key: sm.Secret
    handler_role: iam.Role
    kms_key: kms.Key

    def __init__(self, scope: Construct, construct_id: str, *, props: RestApiStackProps, **kwargs) -> None:
        """
        :param scope: The scope in which this stack is created.
        :param construct_id: The ID of the construct.
        :param props: Properties to customize the REST API stack.
        :param kwargs: Additional keyword arguments.

        """
        super().__init__(scope, construct_id, **kwargs)

        # Create KMS CMK
        self.__create_kms_cmk()
        self.kms_key.apply_removal_policy(props.removal_policy)

        # Create API Key
        self.__create_api_key(kms_cmk=self.kms_key)
        self.api_key.apply_removal_policy(props.removal_policy)

        # Lambda Execution Role
        self.__create_handler_role(removal_policy=props.removal_policy)

        # Lambda
        repo = ecr.Repository.from_repository_name(self, "BedrockLambdaRepo", props.repo_name)
        code = aws_lambda.Code.from_ecr_image(repo)
        props.environment_variables["API_KEY_SECRET_ARN"] = self.api_key.secret_arn
        self.__create_api_handler(
            code=code,
            environment_variables=props.environment_variables,
            function_name=props.api_handler_name
        )
        self.api_handler.apply_removal_policy(props.removal_policy)

        # Cloudformation Outputs
        CfnOutput(
            self, "FunctionName",
            value=self.api_handler.function_name
        )

    def __create_kms_cmk(self):
        # KMS Key
        self.kms_key = kms.Key(
            self, f"EncryptionKey",
            enable_key_rotation=True,
        )

    def __create_api_key(self, kms_cmk: kms.Key):
        # You can create either ssm.StringParameter or ssm.StringListParameters in a CDK app.
        # These are public (not secret) values. Parameters of type SecureString cannot be created
        # directly from a CDK application.[1]  If you want to provision secrets automatically, use
        # Secrets Manager Secrets[2].
        #
        # [1] https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ssm/README.html#creating-new-ssm-parameters-in-your-cdk-app
        # [2] https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_secretsmanager/Secret.html
        self.api_key = sm.Secret(
            self, "api_key",
            encryption_key=kms_cmk,
            generate_secret_string=sm.SecretStringGenerator(
                password_length=256,
                exclude_punctuation=True
            )
        )

    def __create_handler_role(self, removal_policy: RemovalPolicy):
        # IAM Role
        self.handler_role = iam.Role(
            self, "AmazonBedrockApiHandler",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ]
        )
        self.handler_role.apply_removal_policy(removal_policy)
        custom_policy = iam.Policy(
            self, "LambdaCustomExecutionPolicy",
            statements=[
                iam.PolicyStatement.from_json({
                    "Effect": "Allow",
                    "Action": [
                        "kms:Decrypt",
                        "secretsmanager:GetSecretValue"
                    ],
                    "Resource": [
                        self.api_key.secret_arn,
                        self.kms_key.key_arn,
                    ]
                }),
                iam.PolicyStatement.from_json({
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                        "bedrock:ListFoundationModels",
                        "bedrock:ListInferenceProfiles"
                    ],
                    "Resource": "*"
                }),
            ],
        )
        custom_policy.attach_to_role(self.handler_role)
        custom_policy.apply_removal_policy(removal_policy)

    def __create_api_handler(self, code: aws_lambda.Code, environment_variables: dict, function_name: str):
        runtime = aws_lambda.Runtime.FROM_IMAGE
        handler = aws_lambda.Handler.FROM_IMAGE
        arch = aws_lambda.Architecture.ARM_64
        self.api_handler = aws_lambda.Function(
            self, "BedrockLambda",
            function_name=function_name,
            runtime=runtime,  # noqa - IDE reports a type error but it is a false reading
            handler=handler,  # noqa - IDE reports a type error but it is a false reading
            code=code,
            role=self.handler_role,
            timeout=Duration.minutes(15),
            architecture=arch,  # noqa - IDE reports a type error but it is a false reading
            memory_size=1024,
            environment=environment_variables,
        )
