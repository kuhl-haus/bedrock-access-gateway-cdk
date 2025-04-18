<#
.SYNOPSIS
    Sets up CDK stack parameters through environment variables.

.DESCRIPTION
    This script configures all necessary environment variables for CDK stack deployment.
    It provides a standardized way to set up AWS CDK parameters and validates their presence
    before attempting deployment.

.PARAMETER AwsAccountId
    The AWS account ID where resources will be deployed.

.PARAMETER AwsRegion
    The AWS region where resources will be deployed.

.PARAMETER UserName
    Name of the IAM user created for access

.PARAMETER GroupName
    Name of the IAM group where permissions are applied.

.PARAMETER RemovalPolicy
    Specifies the removal policy for AWS resources.

.EXAMPLE
    .\deploy-bedrock-api-users-stack.ps1 `
        -AwsAccountId "987654321098" `
        -AwsRegion "us-west-2" `
        -UserName "BedrockApiUser" `
        -GroupName "BedrockApiUsers" `
        -RemovalPolicy "DESTROY"

.EXAMPLE
    $env:BEDROCK_API_USER_NAME = "BedrockApiUser"
    $env:BEDROCK_API_USERS_GROUP_NAME = "BedrockApiUsers"
    .\deploy-bedrock-api-users-stack.ps1 `
        -AwsAccountId "987654321098" `
        -AwsRegion "us-west-2" `
        -RemovalPolicy "DESTROY"

.NOTES
    Prerequisite: AWS CDK CLI must be installed
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory)]
    [string]$AwsAccountId,

    [string]$AwsRegion="us-west-2",

    [string]$UserName="BedrockApiUser",

    [string]$GroupName="BedrockApiUsers",

    [ValidateSet('DESTROY', 'RETAIN','SNAPSHOT','RETAIN_ON_UPDATE_OR_DELETE')]
    [string]$RemovalPolicy='DESTROY'
)

# Set error action preference to stop on any error
$ErrorActionPreference = 'Stop'

# Create a hashtable of environment variables to set
$envVars = @{
    'AWS_ACCOUNT_ID' = $AwsAccountId
    'AWS_REGION' = $AwsRegion
    'BEDROCK_API_USER_NAME' = $UserName
    'BEDROCK_API_USERS_GROUP_NAME' = $GroupName
    'REMOVAL_POLICY' = $RemovalPolicy
}

# Set environment variables
foreach ($var in $envVars.GetEnumerator()) {
    if ([string]::IsNullOrEmpty($var.Value) -and 
        [string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($var.Key))) {
        throw "Environment variable $($var.Key) is not set and no parameter value was provided"
    }
    if (![string]::IsNullOrEmpty($var.Value)) {
        [Environment]::SetEnvironmentVariable($var.Key, $var.Value)
    }
}

# Execute CDK commands
try {
    Write-Verbose "Executing 'cdk ls'"
    cdk ls
    if ($LASTEXITCODE -ne 0) { throw "cdk ls failed" }

    Write-Verbose "Executing 'cdk deploy'"
    cdk deploy bedrock-api-users --require-approval never --progress events
    if ($LASTEXITCODE -ne 0) { throw "cdk deploy failed" }
}
catch {
    Write-Error -Exception $_.Exception -Message "CDK deployment failed"
    exit 1
}
