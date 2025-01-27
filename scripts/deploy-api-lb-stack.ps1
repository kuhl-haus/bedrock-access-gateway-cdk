<#
.SYNOPSIS
    Sets up CDK stack parameters through environment variables.

.DESCRIPTION
    This script configures all necessary environment variables for CDK stack deployment.
    It provides a standardized way to set up AWS CDK parameters and validates their presence
    before attempting deployment.

.PARAMETER AllowedCidr
    A comma-delimited list of CIDR ranges to allow access from.

.PARAMETER ApiHandlerName
    The name of the API handler.

.PARAMETER ApiHostname
    The hostname for the API.

.PARAMETER AwsAccountId
    The AWS account ID where resources will be deployed.

.PARAMETER AwsRegion
    The AWS region where resources will be deployed.

.PARAMETER EcrRepositoryName
    The name of the ECR repository.

.PARAMETER HostedZoneParentAccount
    The AWS account ID containing the parent hosted zone.

.PARAMETER HostedZoneParentName
    The name of the parent hosted zone.

.PARAMETER HostedZoneName
    The name of the hosted zone to be created.

.PARAMETER EnableCrossRegion
    Enables or disables cross-region inference.

.PARAMETER RemovalPolicy
    Specifies the removal policy for AWS resources.

.EXAMPLE
    .\deploy-api-lb-stack.ps1 `
        -AllowedCidr "127.0.0.1/32" `
        -ApiHandlerName "BedrockAPIHandler" `
        -ApiHostname "proxy" `
        -AwsAccountId "987654321098" `
        -AwsRegion "us-west-2" `
        -EcrRepositoryName "bedrock-proxy-api" `
        -HostedZoneParentAccount "012345678901" `
        -HostedZoneParentName "api.my.tld" `
        -HostedZoneName "bedrock.api.my.tld" `
        -EnableCrossRegion $true `
        -RemovalPolicy "DESTROY"

.EXAMPLE
    $env:ALLOWED_CIDR = "127.0.0.1/32"
    .\deploy-api-lb-stack.ps1 `
        -ApiHandlerName "BedrockAPIHandler" `
        -ApiHostname "proxy" `
        -AwsAccountId "987654321098" `
        -AwsRegion "us-west-2" `
        -EcrRepositoryName "bedrock-proxy-api" `
        -HostedZoneParentAccount "012345678901" `
        -HostedZoneParentName "api.my.tld" `
        -HostedZoneName "bedrock.api.my.tld" `
        -EnableCrossRegion $true `
        -RemovalPolicy "DESTROY"

.NOTES
    Prerequisite: AWS CDK CLI must be installed
#>

[CmdletBinding()]
param (
    [Parameter(Mandatory)]    
    [string]$AllowedCidr,
    
    [Parameter(Mandatory)]
    [string]$AwsAccountId,
    
    [Parameter(Mandatory)]
    [string]$HostedZoneParentAccount,
    
    [Parameter(Mandatory)]
    [string]$HostedZoneParentName,
    
    [Parameter(Mandatory)]
    [string]$HostedZoneName,

    [string]$ApiHandlerName="BedrockAPIHandler",

    [string]$ApiHostname="proxy",

    [string]$AwsRegion="us-west-2",

    [string]$EcrRepositoryName="bedrock-proxy-api",

    [string]$EnableCrossRegion="false",

    [ValidateSet('DESTROY', 'RETAIN','SNAPSHOT','RETAIN_ON_UPDATE_OR_DELETE')]
    [string]$RemovalPolicy='DESTROY'
)

# Set error action preference to stop on any error
$ErrorActionPreference = 'Stop'

# Create a hashtable of environment variables to set
$envVars = @{
    'ALLOWED_CIDR' = $AllowedCidr
    'AWS_ACCOUNT_ID' = $AwsAccountId
    'HOSTED_ZONE_PARENT_ACCOUNT' = $HostedZoneParentAccount
    'HOSTED_ZONE_PARENT_NAME' = $HostedZoneParentName
    'HOSTED_ZONE_NAME' = $HostedZoneName
    'API_HANDLER_NAME' = $ApiHandlerName
    'API_HOSTNAME' = $ApiHostname
    'AWS_REGION' = $AwsRegion
    'ECR_REPOSITORY_NAME' = $EcrRepositoryName
    'ENABLE_CROSS_REGION_INFERENCE' = $EnableCrossRegion
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
    cdk deploy api-lb --require-approval never --progress events
    if ($LASTEXITCODE -ne 0) { throw "cdk deploy failed" }
}
catch {
    Write-Error -Exception $_.Exception -Message "CDK deployment failed"
    exit 1
}