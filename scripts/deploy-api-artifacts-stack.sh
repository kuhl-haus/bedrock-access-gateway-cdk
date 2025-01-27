#!/bin/bash

usage() {
    echo "All CDK stack parameters operate off of environment variables.  "
    echo "The command-line parameters will set or overwrite all needed environment variables."
    echo
    echo "Usage: $0 <--allowed-cidr CIDR> <--aws-account-id ID> <--hosted-zone-parent-account ID> <--hosted-zone-parent-name NAME> <--hosted-zone-name NAME> [options]"
    echo "Required Parameters:"
    echo "  --allowed-cidr CIDR               Set ALLOWED_CIDR"
    echo "  --aws-account-id ID               Set AWS_ACCOUNT_ID"
    echo "  --hosted-zone-parent-account ID   Set HOSTED_ZONE_PARENT_ACCOUNT"
    echo "  --hosted-zone-parent-name NAME    Set HOSTED_ZONE_PARENT_NAME"
    echo "  --hosted-zone-name NAME           Set HOSTED_ZONE_NAME"
    echo
    echo "  Optional Parameters"
    echo "  --api-handler-name NAME           Set API_HANDLER_NAME"
    echo "  --api-hostname HOSTNAME           Set API_HOSTNAME"
    echo "  --aws-region REGION               Set AWS_REGION"
    echo "  --ecr-repository-name NAME        Set ECR_REPOSITORY_NAME"
    echo "  --enable-cross-region BOOL        Set ENABLE_CROSS_REGION_INFERENCE"
    echo "  --removal-policy POLICY           Set REMOVAL_POLICY"
    echo "  -h, --help                        Display this help message"
    echo
    echo "Example:"
    echo "  $0 \\"
    echo "    --allowed-cidr \"127.0.0.1/32\" \\"
    echo "    --aws-account-id \"987654321098\" \\"
    echo "    --hosted-zone-parent-account \"012345678901\" \\"
    echo "    --hosted-zone-parent-name \"api.my.tld\" \\"
    echo "    --hosted-zone-name \"bedrock.api.my.tld\" \\"
    echo
    echo "Example:"
    echo "  $0 \\"
    echo "    --allowed-cidr \"127.0.0.1/32\" \\"
    echo "    --aws-account-id \"987654321098\" \\"
    echo "    --hosted-zone-parent-account \"012345678901\" \\"
    echo "    --hosted-zone-parent-name \"api.my.tld\" \\"
    echo "    --hosted-zone-name \"bedrock.api.my.tld\" \\"
    echo "    --api-handler-name \"BedrockAPIHandler\" \\"
    echo "    --api-hostname \"proxy\" \\"
    echo "    --aws-region \"us-west-2\" \\"
    echo "    --ecr-repository-name \"bedrock-proxy-api\" \\"
    echo "    --enable-cross-region \"true\" \\"
    echo "    --removal-policy \"DESTROY\""
    echo
    echo "Example:"
    echo " $ export ALLOWED_CIDR=\"127.0.0.1/32\" "
    echo
    echo "  $0 \\"
    echo "    --aws-account-id \"987654321098\" \\"
    echo "    --hosted-zone-parent-account \"012345678901\" \\"
    echo "    --hosted-zone-parent-name \"api.my.tld\" \\"
    echo "    --hosted-zone-name \"bedrock.api.my.tld\" \\"
    echo "    --api-handler-name \"BedrockAPIHandler\" \\"
    echo "    --api-hostname \"proxy\" \\"
    echo "    --aws-region \"us-west-2\" \\"
    echo "    --ecr-repository-name \"bedrock-proxy-api\" \\"
    echo "    --enable-cross-region \"true\" \\"
    echo "    --removal-policy \"DESTROY\""
}

while [ $# -gt 0 ]; do
    case "$1" in
        --allowed-cidr)
            export ALLOWED_CIDR="$2"
            shift 2
            ;;
        --api-handler-name)
            export API_HANDLER_NAME="$2"
            shift 2
            ;;
        --api-hostname)
            export API_HOSTNAME="$2"
            shift 2
            ;;
        --aws-account-id)
            export AWS_ACCOUNT_ID="$2"
            shift 2
            ;;
        --aws-region)
            export AWS_REGION="$2"
            shift 2
            ;;
        --ecr-repository-name)
            export ECR_REPOSITORY_NAME="$2"
            shift 2
            ;;
        --hosted-zone-parent-account)
            export HOSTED_ZONE_PARENT_ACCOUNT="$2"
            shift 2
            ;;
        --hosted-zone-parent-name)
            export HOSTED_ZONE_PARENT_NAME="$2"
            shift 2
            ;;
        --hosted-zone-name)
            export HOSTED_ZONE_NAME="$2"
            shift 2
            ;;
        --enable-cross-region)
            export ENABLE_CROSS_REGION_INFERENCE="$2"
            shift 2
            ;;
        --removal-policy)
            export REMOVAL_POLICY="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

set -exu

# Required/non-default environment variables.
env_vars=(
    "ALLOWED_CIDR"
    "AWS_ACCOUNT_ID"
    "HOSTED_ZONE_PARENT_ACCOUNT"
    "HOSTED_ZONE_PARENT_NAME"
    "HOSTED_ZONE_NAME"
)

missing_vars=0

for var in "${env_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "${var} environment variable is not set." >&2
        missing_vars=1
    fi
done

if [ $missing_vars -eq 1 ]; then
    exit 1
fi

cdk ls || exit 1
cdk deploy api-artifacts --require-approval never --progress events || exit 1
