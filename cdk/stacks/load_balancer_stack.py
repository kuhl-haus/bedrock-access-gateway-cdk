from dataclasses import dataclass

from aws_cdk import (
    aws_ec2 as ec2,
    aws_lambda,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as targets,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as r53targets,
    Aws,
    Tags,
    CfnTag,
    RemovalPolicy,
    CfnOutput,
)
from aws_cdk.aws_elasticloadbalancingv2 import SslPolicy, ApplicationListener
from aws_cdk.aws_route53 import IHostedZone
from constructs import Construct

from cdk.stacks.base_stack import BaseStack


@dataclass
class LoadBalancerStackProps:
    """
    A dataclass defining the properties for a Load Balancer Stack.

    Attributes
    ----------
    allowed_cidr : list of str
        List of CIDR blocks allowed to access the load balancer.
    api_handler : aws_lambda.Function
        The AWS Lambda function serving as API handler.
    api_hostname : str
        The hostname for the API.
    hosted_zone_id : str
        The ID of the hosted zone where the domain is managed.
    hosted_zone_name : str
        The name of the hosted zone where the domain is managed.
    removal_policy : RemovalPolicy
        Policy that defines what happens to the resources when the stack is destroyed.
    """
    allowed_cidr: [str]
    api_handler: aws_lambda.Function
    api_hostname: str
    hosted_zone_id: str
    hosted_zone_name: str
    removal_policy: RemovalPolicy


class LoadBalancerStack(BaseStack):
    """
        A class that represents a load balancer stack with associated resources such as VPC, TLS certificate, security group, load balancer, etc.

        Attributes
        ----------
        dns_alias : route53.ARecord
            DNS alias for the load balancer.
        tls_cert : acm.Certificate
            TLS certificate for securing HTTPS traffic.
        load_balancer : elbv2.ApplicationLoadBalancer
            Application load balancer to route traffic.
        security_group : ec2.SecurityGroup
            Security group associated with the load balancer.
        target_group : elbv2.ApplicationTargetGroup
            Target group for the load balancer to direct traffic.
        vpc : ec2.Vpc
            Virtual private cloud for the stack.
    """
    dns_alias: route53.ARecord
    tls_cert: acm.Certificate
    load_balancer: elbv2.ApplicationLoadBalancer
    security_group: ec2.SecurityGroup
    target_group: elbv2.ApplicationTargetGroup
    vpc: ec2.Vpc

    def __init__(self, scope: Construct, construct_id: str, *, props: LoadBalancerStackProps, **kwargs) -> None:
        """
        :param scope: The scope in which this construct is defined.
        :type scope: Construct
        :param construct_id: The scoped ID of the construct.
        :type construct_id: str
        :param props: Properties specific to the LoadBalancerStack.
        :type props: LoadBalancerStackProps
        :param kwargs: Additional keyword arguments.
        :type kwargs: dict
        """
        super().__init__(scope, construct_id, **kwargs)
        # VPC
        self.__create_vpc(construct_id)
        self.vpc.apply_removal_policy(props.removal_policy)

        # Security Group
        self.__create_sg(vpc=self.vpc, allowed_cidr=props.allowed_cidr)
        self.security_group.apply_removal_policy(props.removal_policy)

        # TLS Certificate
        zone = route53.PublicHostedZone.from_hosted_zone_attributes(
            self, "Zone",
            hosted_zone_id=props.hosted_zone_id,
            zone_name=props.hosted_zone_name,
        )
        domain_name = f"{props.api_hostname}.{props.hosted_zone_name}"
        self.__create_certificate(zone=zone, domain_name=domain_name)
        self.tls_cert.apply_removal_policy(props.removal_policy)

        # Lambda Load Balancer
        self.__create_load_balancer(
            vpc=self.vpc,
            security_group=self.security_group,
            function_name=props.api_handler.function_name
        )
        self.load_balancer.apply_removal_policy(props.removal_policy)

        # HTTP Listener
        http_listener = self.__add_http_redirect()
        http_listener.apply_removal_policy(props.removal_policy)

        # HTTPS Listener
        https_listener = self.__add_https_listener(tls_cert=self.tls_cert)
        https_listener.apply_removal_policy(props.removal_policy)

        # Create DNS alias for load balancer
        self.__create_dns_alias(zone=zone, record_name=props.api_hostname)
        self.dns_alias.apply_removal_policy(props.removal_policy)

        # Cloudformation Outputs
        CfnOutput(
            self, "CertificateArn",
            value=self.tls_cert.certificate_arn
        )

        CfnOutput(
            self, "LoadBalancerDNS",
            value=self.load_balancer.load_balancer_dns_name
        )

        CfnOutput(
            self, "LoadBalancerAlias",
            value=self.dns_alias.domain_name
        )

    def __create_certificate(self, zone: IHostedZone, domain_name: str):
        self.tls_cert = acm.Certificate(
            self, "Certificate",
            domain_name=domain_name,
            validation=acm.CertificateValidation.from_dns(zone)
        )

    def __create_load_balancer(self, vpc: ec2.Vpc, security_group: ec2.SecurityGroup, function_name: str):
        # Application Load Balancer
        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self, "LoadBalancer",
            vpc=vpc,
            internet_facing=True,
            security_group=security_group,
        )
        # Target Group
        self.target_group = elbv2.ApplicationTargetGroup(
            self, "LambdaTargetGroup",
            vpc=vpc,
            targets=[],
            target_type=elbv2.TargetType.LAMBDA,
        )
        lambda_target = aws_lambda.Function.from_function_name(
            self, "LambdaFunction",
            function_name=function_name
        )
        self.target_group.add_target(targets.LambdaTarget(lambda_target))

    def __create_dns_alias(self, zone: IHostedZone, record_name: str):
        target = route53.RecordTarget.from_alias(
            r53targets.LoadBalancerTarget(self.load_balancer)
        )
        self.dns_alias = route53.ARecord(
            self, "AliasRecord",
            zone=zone,
            target=target,
            record_name=record_name,
            delete_existing=True,
        )

    def __add_http_redirect(self) -> ApplicationListener:
        # HTTP Listener
        listener = self.load_balancer.add_listener(
            "ListenerHTTP",
            port=80,
            open=False
        )
        listener.add_action(
            "DefaultRedirect",
            action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True
            )
        )
        return listener

    def __add_https_listener(self, tls_cert: acm.Certificate) -> ApplicationListener:
        # HTTPS Listener
        listener = self.load_balancer.add_listener(
            "ListenerHTTPS",
            port=443,
            open=False,
            certificates=[tls_cert],
            ssl_policy=SslPolicy.FORWARD_SECRECY  # Use RECOMMENDED_TLS if FORWARD_SECRECY doesn't work.
        )
        listener.add_target_groups(
            "LambdaTargetGroupAttachment",
            target_groups=[self.target_group]
        )
        return listener

    def __create_vpc(self, construct_id: str):
        self.vpc = ec2.Vpc(
            self, f"{construct_id}-vpc",
            nat_gateways=0,
            ip_addresses=ec2.IpAddresses.cidr('172.28.16.0/22'),
            subnet_configuration=[
                {
                    "cidrMask": 24,
                    "name": "public",
                    "subnetType": ec2.SubnetType.PUBLIC,
                },
            ],
            vpc_name=self.format_name("{}", [construct_id])
        )
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SubnetType.html

    def __create_sg(self, vpc: ec2.Vpc, allowed_cidr: [str]):
        # Security Group
        self.security_group = ec2.SecurityGroup(
            self,
            "ALBSecurityGroup",
            vpc=vpc,
            description=f"Security Group for {Aws.STACK_NAME}",
            allow_all_outbound=True,
        )

        for cidr in allowed_cidr:
            self.security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(cidr),
                connection=ec2.Port.tcp(80),
                description=f"Allow {cidr} on port 80"
            )

            self.security_group.add_ingress_rule(
                peer=ec2.Peer.ipv4(cidr),
                connection=ec2.Port.tcp(443),
                description=f"Allow {cidr} on port 443"
            )
