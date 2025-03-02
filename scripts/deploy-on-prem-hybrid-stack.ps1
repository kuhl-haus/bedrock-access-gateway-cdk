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

.PARAMETER SecretArnParameter
    Name of the SSM Parameter to put the Secret ARN containing the API key.

.PARAMETER RemovalPolicy
    Specifies the removal policy for AWS resources.

.EXAMPLE
    .\deploy-api-artifacts-stack.ps1 `
        -AwsAccountId "987654321098" `
        -AwsRegion "us-west-2" `
        -SecretArnParameter "MyBerockApiKey" `
        -RemovalPolicy "DESTROY"

.EXAMPLE
    $env:SECRET_ARN_PARAMETER = "MyBerockApiKey"
    .\deploy-api-artifacts-stack.ps1 `
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

    [string]$SecretArnParameter="BedrockApiKey",

    [ValidateSet('DESTROY', 'RETAIN','SNAPSHOT','RETAIN_ON_UPDATE_OR_DELETE')]
    [string]$RemovalPolicy='DESTROY'
)

# Set error action preference to stop on any error
$ErrorActionPreference = 'Stop'

# Create a hashtable of environment variables to set
$envVars = @{
    'AWS_ACCOUNT_ID' = $AwsAccountId
    'AWS_REGION' = $AwsRegion
    'SECRET_ARN_PARAMETER' = $SecretArnParameter
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
    cdk deploy on-prem --require-approval never --progress events
    if ($LASTEXITCODE -ne 0) { throw "cdk deploy failed" }
}
catch {
    Write-Error -Exception $_.Exception -Message "CDK deployment failed"
    exit 1
}