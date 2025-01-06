from dataclasses import dataclass

from aws_cdk import (
    RemovalPolicy,
    aws_ecr as ecr,
    CfnOutput,
)
from constructs import Construct

from cdk.stacks.base_stack import BaseStack


@dataclass
class ArtifactsStackProps:
    """
    Represents the properties for creating an Artifacts Stack.

    Attributes
    ----------
    repo_name : str
        The name of the repository.
    removal_policy : RemovalPolicy
        The policy to apply when the stack is removed.
    """
    repo_name: str
    removal_policy: RemovalPolicy


class ArtifactsStack(BaseStack):
    """
    A stack for managing and creating an ECR (Elastic Container Registry) repository.

    Repository: ecr.Repository
        The ECR repository created by this stack.
    """
    repository: ecr.Repository

    def __init__(self, scope: Construct, construct_id: str, *, props: ArtifactsStackProps, **kwargs) -> None:
        """
        :param scope: The scope in which this construct is defined.
        :param construct_id: The ID of the construct within the scope.
        :param props: Properties to configure the ArtifactsStack.
        :param kwargs: Additional keyword arguments.
        """
        super().__init__(scope, construct_id, **kwargs)
        self.__create_repository(self.format_name("{}", [props.repo_name]))
        self.repository.apply_removal_policy(props.removal_policy)

        CfnOutput(
            self, "RepositoryArn",
            value=self.repository.repository_arn
        )
        CfnOutput(
            self, "RepositoryName",
            value=self.repository.repository_name
        )
        CfnOutput(
            self, "RepositoryUri",
            value=self.repository.repository_uri
        )

    def __create_repository(self, repo_name):
        """
        :param repo_name: The name of the ECR repository to create.
        :return: None
        """
        self.repository = ecr.Repository(self, "Repository", repository_name=repo_name)
        self.repository.add_lifecycle_rule(rule_priority=1, max_image_count=5)
