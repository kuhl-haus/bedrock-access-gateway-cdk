from dataclasses import dataclass

from aws_cdk import (
    aws_iam as iam,
    aws_kms as kms,
    aws_secretsmanager as sm,
    aws_ssm as ssm,
    RemovalPolicy,
    CfnOutput,
    SecretValue,
)
from constructs import Construct

from cdk.stacks.base_stack import BaseStack


@dataclass
class OnPremHybridStackProps:
    """
    Represents the properties required to define an OnPremHybridStack.

    Attributes:
        secret_arn_parameter: The name of the SSM parameter to use.
        removal_policy (RemovalPolicy): The policy that defines what happens to the stack when removed.
    """
    secret_arn_parameter: str
    removal_policy: RemovalPolicy


class OnPremHybridStack(BaseStack):
    """
    Class for creating resources for accessing Bedrock from on-prem.
    """
    api_key: sm.Secret
    iam_user: iam.User
    iam_group: iam.Group
    kms_key: kms.Key
    param: ssm.StringParameter

    def __init__(self, scope: Construct, construct_id: str, *, props: OnPremHybridStackProps, **kwargs) -> None:
        """
        :param scope: The scope in which this stack is created.
        :param construct_id: The ID of the construct.
        :param props: Properties to customize the REST API stack.
        :param kwargs: Additional keyword arguments.

        """
        super().__init__(scope, construct_id, **kwargs)

        # Create KMS CMK
        self.__create_kms_cmk(removal_policy=props.removal_policy)

        # Create API Key
        self.__create_api_key(kms_cmk=self.kms_key, removal_policy=props.removal_policy)
        self.__create_ssm_parameter(
            api_key=self.api_key, name=props.secret_arn_parameter, removal_policy=props.removal_policy
        )

        # IAM Access
        self.__create_iam_user(kms_cmk=self.kms_key, removal_policy=props.removal_policy)

        # Cloudformation Outputs
        CfnOutput(
            self, "UserArn",
            value=self.iam_user.user_arn
        )

    def __create_kms_cmk(self, removal_policy: RemovalPolicy):
        # KMS Key
        self.kms_key = kms.Key(
            self, f"EncryptionKey",
            enable_key_rotation=True,
        )
        self.kms_key.apply_removal_policy(removal_policy)

    def __create_api_key(self, kms_cmk: kms.Key, removal_policy: RemovalPolicy):
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
        self.api_key.apply_removal_policy(removal_policy)

    def __create_ssm_parameter(self, name: str, api_key: sm.Secret, removal_policy: RemovalPolicy):
        self.param = ssm.StringParameter(
            self, "ApiKeyParameter", parameter_name=name, simple_name=True, string_value=api_key.secret_arn,
        )
        self.param.apply_removal_policy(removal_policy)

    def __create_iam_user(self, kms_cmk: kms.Key, removal_policy: RemovalPolicy):
        # IAM Group
        self.iam_group = iam.Group(
            self, "BedrockApiUsers",
            group_name="BedrockApiUsers"
        )
        self.iam_group.apply_removal_policy(removal_policy)

        # IAM Policy
        bedrock_policy = iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        self.iam_group.add_managed_policy(bedrock_policy)

        custom_policy = iam.Policy(
            self, "BedrockApiUserPolicy",
            statements=[
                iam.PolicyStatement.from_json({
                    "Effect": "Allow",
                    "Action": [
                        "kms:Decrypt",
                        "secretsmanager:GetSecretValue",
                        "ssm:Get*",
                        "ssm:Describe*",
                    ],
                    "Resource": [
                        self.api_key.secret_arn,
                        self.kms_key.key_arn,
                        self.param.parameter_arn
                    ]
                })
            ],
        )
        custom_policy.apply_removal_policy(removal_policy)
        custom_policy.attach_to_group(self.iam_group)

        # IAM User
        self.iam_user = iam.User(
            self, "BedrockApiUser",
            user_name="BedrockApiUser"
        )
        self.iam_user.apply_removal_policy(removal_policy)
        self.iam_user.add_to_group(self.iam_group)

        # Note: this is not very secure - only use for proof-of-concept/initial testing.
        # Disable these keys as soon as possible.
        access_key = iam.CfnAccessKey(
            self, "BedrockApiUserAccessKey",
            user_name=self.iam_user.user_name
        )
        secret_value = {
            "AccessKeyId": SecretValue.unsafe_plain_text(access_key.ref),
            "SecretAccessKey": SecretValue.unsafe_plain_text(access_key.attr_secret_access_key),
        }
        sm.Secret(
            self, "iam_access_key",
            encryption_key=kms_cmk,
            secret_object_value=secret_value
        )
