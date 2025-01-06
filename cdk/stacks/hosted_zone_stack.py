from dataclasses import dataclass

from aws_cdk import (
    aws_route53 as route53,
    aws_iam as iam,
    RemovalPolicy, CfnOutput, Stack,
)
from constructs import Construct

from cdk.stacks.base_stack import BaseStack


@dataclass
class HostedZoneStackProps:
    """
    Class to represent the properties for a hosted zone stack.

    Attributes:
        hosted_zone_name (str): The name of the hosted zone.
        hosted_zone_parent_name (str): The name of the parent hosted zone.
        hosted_zone_parent_account (str): The account ID of the parent hosted zone.
        delegation_role_name (str): The name of the delegation role.
    """
    hosted_zone_name: str
    hosted_zone_parent_name: str
    hosted_zone_parent_account: str
    delegation_role_name: str


class HostedZoneStack(BaseStack):
    """
    class HostedZoneStack(BaseStack):
        Manages the creation and configuration of a Route 53 hosted zone within an AWS CloudFormation stack.

        :param scope: The parent construct, usually `App` or `Stack`, representing the scope in which this construct is defined.
        :param construct_id: The unique identifier for this construct within the given scope.
        :param props: The properties for configuring the hosted zone stack, encapsulated in `HostedZoneStackProps`.
        :param kwargs: Additional keyword arguments passed to the base class.

        def __init__(self, scope: Construct, construct_id: str, *, props: HostedZoneStackProps, **kwargs) -> None:
            Initializes the HostedZoneStack, creates a hosted zone, applies a strict removal policy,
            and outputs the created hosted zone's ID and name.

            :param scope: The parent construct, usually `App` or `Stack`, representing the scope in which this construct is defined.
            :param construct_id: The unique identifier for this construct within the given scope.
            :param props: The properties for configuring the hosted zone stack, encapsulated in `HostedZoneStackProps`.
            :param kwargs: Additional keyword arguments passed to the base class.

        def __create_delegated_zone(self, construct_id, hosted_zone_name: str):
            Creates a Route 53 hosted zone with the specified name.

            :param construct_id: The unique identifier for the constructed resource.
            :param hosted_zone_name: The name of the DNS zone to be hosted.
            :return: A Route 53 hosted zone object created with the given parameters.

        def __create_zone_delegation(self, hosted_zone_parent_account, delegation_role_name, hosted_zone_parent_name):
            Creates a delegation record in the parent hosted zone to refer to the hosted zone managed by this stack.

            :param hosted_zone_parent_account: The AWS account ID of the parent hosted zone.
            :param delegation_role_name: The IAM role name used for delegation in the parent account.
            :param hosted_zone_parent_name: The name of the parent DNS zone.
    """
    zone: route53.IHostedZone

    def __init__(self, scope: Construct, construct_id: str, *, props: HostedZoneStackProps, **kwargs) -> None:
        """
        :param scope: The parent construct, usually `App` or `Stack`, representing the scope in which this construct is defined.
        :param construct_id: The unique identifier for this construct within the given scope.
        :param props: The properties for configuring the hosted zone stack, encapsulated in `HostedZoneStackProps`.
        :param kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(scope, construct_id, **kwargs)
        # Hosted Zone
        self.__create_delegated_zone(construct_id, hosted_zone_name=props.hosted_zone_name)
        #######################################################################
        #     DANGER ZONE  -  DANGER ZONE  -  DANGER ZONE  -  DANGER ZONE     #
        #######################################################################
        # DO NOT CHANGE THE REMOVAL POLICY UNLESS YOU:
        # 1. !!!! UNDERSTAND THIS PROCESS TAKES DAYS !!!!
        # 2. DECOMMISSION ALL TLS CERTIFICATES ASSOCIATED WITH THE DOMAIN
        # 3. REMOVE THE DELEGATION FROM THE ROOT DOMAIN
        # 4. WAIT FOR THE CACHE TTL TO EXPIRE GLOBALLY
        # 5. VERIFY MULTIPLE TIMES THAT THE ABOVE IS COMPLETE
        # 6. ... are you sure?
        # 7. How can you be so sure? (where is your evidence?)
        # 8. OK, if you're really, really sure... go ahead.
        self.zone.apply_removal_policy(RemovalPolicy.RETAIN)
        # DO NOT CHANGE THE REMOVAL POLICY UNLESS YOU READ EVERYTHING ABOVE IT
        #######################################################################
        #     DANGER ZONE  -  DANGER ZONE  -  DANGER ZONE  -  DANGER ZONE     #
        #######################################################################

        # Cloudformation Stack Outputs
        self.__create_zone_delegation(
            props.hosted_zone_parent_account,
            props.delegation_role_name,
            props.hosted_zone_parent_name
        )
        CfnOutput(
            self, "HostedZoneId",
            value=self.zone.hosted_zone_id
        )
        CfnOutput(
            self, "HostedZoneName",
            value=props.hosted_zone_name
        )

    def __create_delegated_zone(self, construct_id, hosted_zone_name: str):
        """
        :param construct_id: The unique identifier for the constructed resource.
        :param hosted_zone_name: The name of the DNS zone to be hosted.
        :return: A Route 53 hosted zone object created with the given parameters.
        """
        self.zone = route53.HostedZone(
            self, f"{construct_id}-zone",
            zone_name=hosted_zone_name
        )

    def __create_zone_delegation(self, hosted_zone_parent_account, delegation_role_name, hosted_zone_parent_name):
        # import the delegation role by constructing the roleArn
        delegation_role_arn = Stack.of(self).format_arn(
            region="",  # IAM is global in each partition
            service="iam",
            account=hosted_zone_parent_account,
            resource="role",
            resource_name=delegation_role_name
        )
        delegation_role = iam.Role.from_role_arn(self, "DelegationRole", delegation_role_arn)

        # create the record
        route53.CrossAccountZoneDelegationRecord(
            self, "delegate",
            delegated_zone=self.zone,
            parent_hosted_zone_name=hosted_zone_parent_name,
            # or you can use parentHostedZoneId
            delegation_role=delegation_role
        )
