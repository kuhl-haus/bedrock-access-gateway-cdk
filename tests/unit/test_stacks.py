import aws_cdk as core
import aws_cdk.assertions as assertions


def test_importable():
    from cdk.stacks.artifacts_stack import ArtifactsStack
    from cdk.stacks.base_stack import BaseStack
    from cdk.stacks.load_balancer_stack import LoadBalancerStack
    from cdk.stacks.hosted_zone_stack import HostedZoneStack
    from cdk.stacks.rest_api_stack import RestApiStack
