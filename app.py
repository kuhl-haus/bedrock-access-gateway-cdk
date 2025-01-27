#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import RemovalPolicy

from cdk.stacks.base_stack import BillingTag
from cdk.stacks.artifacts_stack import ArtifactsStack, ArtifactsStackProps
from cdk.stacks.hosted_zone_stack import HostedZoneStack, HostedZoneStackProps
from cdk.stacks.load_balancer_stack import LoadBalancerStack, LoadBalancerStackProps
from cdk.stacks.r53_delegate_role_stack import R53DelegateRoleStack, R53DelegateRoleStackProps
from cdk.stacks.rest_api_stack import RestApiStack, RestApiStackProps


def get_environment_variable(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} not set")
    return value


def get_removal_policy(default=None):
    policy = get_environment_variable("REMOVAL_POLICY", default=default)
    if policy == "RETAIN":
        return RemovalPolicy.RETAIN
    elif policy == "SNAPSHOT":
        return RemovalPolicy.SNAPSHOT
    elif policy == "RETAIN_ON_UPDATE_OR_DELETE":
        return RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE
    else:
        return RemovalPolicy.DESTROY


###############################################################################
# Environment
# The environment variables used here are available as a method to inject different values at runtime. 
###############################################################################
# Root DNS Account - This is the account where the parent DNS zone that will delegate to the deployment account.
hosted_zone_parent_account = get_environment_variable("HOSTED_ZONE_PARENT_ACCOUNT")
hosted_zone_parent_name = get_environment_variable("HOSTED_ZONE_PARENT_NAME")

# Deployment Account - This is the account where the Bedrock API, Lambda, etc. will be deployed.
aws_account_id = get_environment_variable("AWS_ACCOUNT_ID")
hosted_zone_name = get_environment_variable("HOSTED_ZONE_NAME")

# Even with a strong API key, I recommend locking this down to only trusted IP ranges.  This is applied to the ALB security group.
allowed_cidr = get_environment_variable("ALLOWED_CIDR").split(',')

# These values are compatible with the values from the aws-samples/bedrock-access-gateway CFN template
api_handler_name = get_environment_variable("API_HANDLER_NAME", "BedrockAPIHandler")
api_hostname = get_environment_variable("API_HOSTNAME", "proxy")
aws_region = get_environment_variable("AWS_REGION", "us-west-2")
repo_name = get_environment_variable("ECR_REPOSITORY_NAME", "bedrock-proxy-api")
enable_cross_region_inference = get_environment_variable("ENABLE_CROSS_REGION_INFERENCE", "false")
removal_policy = get_removal_policy("DESTROY")


# https://docs.aws.amazon.com/cdk/latest/guide/environments.html
env = cdk.Environment(account=aws_account_id, region=aws_region)
app = cdk.App()
billing_tag = BillingTag("BedrockAPI")
delegation_role_name = f"r53_{hosted_zone_name}_{aws_account_id}"
# DNS Delegate Role - IAM Role to enable cross-account delegation
delegation_role_stack_name = delegation_role_name.replace(".", "-")
delegation_role_stack_name = delegation_role_stack_name.replace("_", "-")
r53_role = R53DelegateRoleStack(app, delegation_role_stack_name, **{
    "env": cdk.Environment(account=hosted_zone_parent_account, region=aws_region),
    "billing_tag": billing_tag,
    "props": R53DelegateRoleStackProps(
        hosted_zone_parent_name=hosted_zone_parent_name,
        delegation_role_name=delegation_role_name,
        delegation_account_id=aws_account_id,
        removal_policy=removal_policy,
    )
})
###############################################################################
#  DANGER - DANGER    DEPLOY THE DNS STACK ONE TIME ONLY!    DANGER - DANGER  #
###############################################################################
# DNS Stack - Delegated zone
dns = HostedZoneStack(app, "dns-stack", **{
    "env": env, "billing_tag": billing_tag,
    "props": HostedZoneStackProps(
        hosted_zone_name=hosted_zone_name,
        hosted_zone_parent_name=hosted_zone_parent_name,
        hosted_zone_parent_account=hosted_zone_parent_account,
        delegation_role_name=delegation_role_name,
    )
})
###############################################################################
# Artifacts Stack - ECR Repository
artifacts = ArtifactsStack(app, "api-artifacts", **{
    "env": env, "billing_tag": billing_tag,
    "props": ArtifactsStackProps(
        repo_name=repo_name, removal_policy=removal_policy
    )
})

###############################################################################
#   SERVICE STACKS  -  SERVICE STACKS  -  SERVICE STACKS  -  SERVICE STACKS   #
###############################################################################
# REST API Stack - Lambda, IAM Role, API Key and KMS CMK
api = RestApiStack(app, "api-handler", **{
    "env": env, "billing_tag": billing_tag,
    "props": RestApiStackProps(
        api_handler_name=api_handler_name,
        repo_name=artifacts.repository.repository_name,
        removal_policy=removal_policy,
        environment_variables={"ENABLE_CROSS_REGION_INFERENCE": enable_cross_region_inference},
    ),
})
###############################################################################
# TLS Certificate and Load Balancer Stack
lb = LoadBalancerStack(app, "api-lb", **{
    "env": env, "billing_tag": billing_tag,
    "props": LoadBalancerStackProps(
        allowed_cidr=allowed_cidr,
        api_handler=api.api_handler,
        api_hostname=api_hostname,
        hosted_zone_id=dns.zone.hosted_zone_id,
        hosted_zone_name=dns.zone.zone_name,
        removal_policy=removal_policy,
    )
})
###############################################################################
app.synth()
