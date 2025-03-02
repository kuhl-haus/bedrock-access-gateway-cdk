#!/bin/bash

usage() {
    echo "All CDK stack parameters operate off of environment variables.  "
    echo "The command-line parameters will set or overwrite all needed environment variables."
    echo
    echo "Usage: $0 <--aws-account-id ID> [options]"
    echo "Required Parameters:"
    echo "  --aws-account-id ID               Set AWS_ACCOUNT_ID"
    echo
    echo "  Optional Parameters"
    echo "  --aws-region REGION               Set AWS_REGION"
    echo "  --secret-arn-parameter NAME       Set SECRET_ARN_PARAMETER"
    echo "  --removal-policy POLICY           Set REMOVAL_POLICY"
    echo "  -h, --help                        Display this help message"
    echo
    echo "Example:"
    echo "  $0 \\"
    echo "    --aws-account-id \"987654321098\" \\"
    echo
    echo "Example:"
    echo "  $0 \\"
    echo "    --aws-account-id \"987654321098\" \\"
    echo "    --aws-region \"us-west-2\" \\"
    echo "    --secret-arn-parameter \"MyBedrockApiKey\" \\"
    echo "    --removal-policy \"DESTROY\""
    echo
    echo "Example:"
    echo " $ export SECRET_ARN_PARAMETER=\"MyBedrockApiKey\" "
    echo
    echo "  $0 \\"
    echo "    --aws-account-id \"987654321098\" \\"
    echo "    --aws-region \"us-west-2\" \\"
    echo "    --removal-policy \"DESTROY\""
}

while [ $# -gt 0 ]; do
    case "$1" in
        --aws-account-id)
            export AWS_ACCOUNT_ID="$2"
            shift 2
            ;;
        --aws-region)
            export AWS_REGION="$2"
            shift 2
            ;;
        --secret-arn-parameter)
            export SECRET_ARN_PARAMETER="$2"
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
    "AWS_ACCOUNT_ID"
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
cdk deploy on-prem --require-approval never --progress events || exit 1
