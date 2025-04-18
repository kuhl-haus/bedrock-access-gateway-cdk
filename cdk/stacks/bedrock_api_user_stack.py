from dataclasses import dataclass

from aws_cdk import (
    aws_iam as iam,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

from cdk.stacks.base_stack import BaseStack


@dataclass
class BedrockApiUserStackProps:
    user_name: str
    group_name: str
    removal_policy: RemovalPolicy


class BedrockApiUserStack(BaseStack):
    iam_user: iam.User
    iam_group: iam.Group

    def __init__(self, scope: Construct, construct_id: str, *, props: BedrockApiUserStackProps, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.__create_iam_group(group_name=props.group_name, removal_policy=props.removal_policy)
        self.__create_iam_user(user_name=props.user_name, removal_policy=props.removal_policy)

        # Cloudformation Outputs
        CfnOutput(
            self, "UserArn",
            value=self.iam_user.user_arn
        )
        CfnOutput(
            self, "GroupArn",
            value=self.iam_group.group_arn
        )

    def __create_iam_group(self, group_name: str, removal_policy: RemovalPolicy):
        self.iam_group = iam.Group(
            self, "BedrockApiUsers",
            group_name=group_name,
        )
        self.iam_group.apply_removal_policy(removal_policy)

        bedrock_policy = iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        self.iam_group.add_managed_policy(bedrock_policy)

    def __create_iam_user(self, user_name: str, removal_policy: RemovalPolicy):
        self.iam_user = iam.User(
            self, "BedrockApiUser",
            user_name=user_name
        )
        self.iam_user.apply_removal_policy(removal_policy)
        self.iam_user.add_to_group(self.iam_group)
