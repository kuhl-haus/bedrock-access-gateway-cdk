from dataclasses import dataclass

from aws_cdk import (
    aws_route53 as route53,
    aws_iam as iam,
    RemovalPolicy, CfnOutput, Stack,
)
from constructs import Construct

from cdk.stacks.base_stack import BaseStack


@dataclass
class R53DelegateRoleStackProps:
    """
    Class to represent the properties for a Route 53 delegation role stack.

    Attributes:
        hosted_zone_parent_name (str): The name of the parent hosted zone.
        delegation_role_name (str): The name of the delegation role.
        removal_policy (RemovalPolicy): Defines what happens to the resources when the stack is destroyed.
    """
    hosted_zone_parent_name: str
    delegation_role_name: str
    delegation_account_id: str
    removal_policy: RemovalPolicy


class R53DelegateRoleStack(BaseStack):
    role: iam.Role

    def __init__(self, scope: Construct, construct_id: str, *, props: R53DelegateRoleStackProps, **kwargs) -> None:
        """
        Manages the creation and configuration of an IAM role with permissions to create delegation records.

        :param scope: The parent construct, usually `App` or `Stack`, representing the scope in which this construct is defined.
        :param construct_id: The unique identifier for this construct within the given scope.
        :param props: The properties for configuring the hosted zone stack, encapsulated in `HostedZoneStackProps`.
        :param kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(scope, construct_id, **kwargs)
        # Hosted Zone
        self.__create_role(
            construct_id,
            delegation_role_name=props.delegation_role_name,
            delegation_account_id=props.delegation_account_id,
            hosted_zone_name=props.hosted_zone_parent_name,
            removal_policy=props.removal_policy,
        )

        CfnOutput(
            self, "DelegateRoleArn",
            value=self.role.role_arn,
        )
        CfnOutput(
            self, "DelegateRoleName",
            value=self.role.role_name
        )

    def __create_role(self, construct_id, delegation_role_name, delegation_account_id, hosted_zone_name: str, removal_policy: RemovalPolicy):
        # IAM Role
        self.role = iam.Role(
            self, "r53delegate",
            role_name=delegation_role_name,
            assumed_by=iam.ArnPrincipal(f"arn:aws:iam::{delegation_account_id}:root")
        )
        self.role.apply_removal_policy(removal_policy)
        hosted_zone = route53.HostedZone.from_lookup(
            self, id=f"{construct_id}-zone-parent",
            domain_name=hosted_zone_name
        )
        custom_policy = iam.Policy(
            self, "r53DelegatePolicy",
            statements=[
                iam.PolicyStatement.from_json({
                    "Effect": "Allow",
                    "Action": [
                        "route53:GetHostedZone",
                        "route53:ChangeResourceRecordSets",
                        "route53:ListResourceRecordSets"
                    ],
                    "Resource": [
                        hosted_zone.hosted_zone_arn
                    ]
                }),
                iam.PolicyStatement.from_json({
                    "Effect": "Allow",
                    "Action": [
                        "route53:TestDNSAnswer",
                        "route53:ListHostedZones",
                        "route53:GetHostedZoneCount",
                        "route53:ListHostedZonesByName"
                    ],
                    "Resource": "*"
                }),
            ],
        )
        custom_policy.attach_to_role(self.role)
        custom_policy.apply_removal_policy(removal_policy)
