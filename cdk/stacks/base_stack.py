import hashlib
from typing import List

from aws_cdk import Stack
from aws_cdk import Tags
from constructs import Construct


MAX_NAME_LENGTH = 128


class BillingTag:
    key: str
    value: str

    def __init__(self, value: str):
        self.key = "Billing"
        self.value = value


class BaseStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, billing_tag: BillingTag, **kwargs) -> None:
        """
        :param scope: The scope in which this construct is defined.
        :param construct_id: The unique identifier for this construct.
        :param billing_tag: The billing tag to be associated with this construct, containing key and value.
        :param kwargs: Additional keyword arguments to be passed to the parent class constructor.
        """
        super().__init__(scope, construct_id, **kwargs)
        Tags.of(self).add(billing_tag.key, billing_tag.value)

    @classmethod
    def format_name(cls, template: str, params: List[str]) -> str:
        """
        :param template: The template string used for formatting the name.
        :param params: A list of strings that will be used to format the template.
        :return: A formatted name string. If the length exceeds 64 characters, the name is truncated and hashed.
        """
        if not isinstance(template, str):
            raise ValueError("Template must be a string")

        if not isinstance(params, list) or not all(isinstance(param, str) for param in params):
            raise ValueError("Params must be a list of strings")

        return cls.__return_formatted_name(template.format(*params))

    @classmethod
    def format_name_kw(cls, template: str, params: dict) -> str:
        """
        :param template: Template string to be formatted.
        :param params: Dictionary containing the parameters to format the template.
        :return: Formatted string with parameter values inserted, truncated and hashed if length exceeds 64 characters.
        """
        if not isinstance(template, str):
            raise ValueError("Template must be a string")

        if not isinstance(params, dict):
            raise ValueError("Params must be a dictionary")

        return cls.__return_formatted_name(template.format(**params))

    @classmethod
    def __return_formatted_name(cls, name: str) -> str:
        if len(name) > MAX_NAME_LENGTH:
            old_name = name
            name = cls.__truncate_and_hash(name)
            print(f"WARNING: TRUNCATED NAME {old_name} -TO-> {name}")
        return name

    @staticmethod
    def __truncate_and_hash(name: str) -> str:
        first_part_length = MAX_NAME_LENGTH - 6
        first_part = name[:first_part_length]
        remaining_part = name[first_part_length:].encode('utf-8')
        hashed_part = hashlib.sha256(remaining_part).hexdigest()[:6]
        return f"{first_part}{hashed_part}"
