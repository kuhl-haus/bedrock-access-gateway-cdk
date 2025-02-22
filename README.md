
# bedrock-access-gateway-cdk

Example CDK to deploy AWS Lambda infrastructure that is compatible aws-samples/bedrock-access-gateway at [aws-samples/bedrock-access-gateway](https://github.com/aws-samples/bedrock-access-gateway).

What's included:
* ECR Repository ([artifacts_stack.py](https://github.com/kuhl-haus/bedrock-access-gateway-cdk/blob/mainline/cdk/stacks/artifacts_stack.py))
* Route53 Hosted Zone ([hosted_zone_stack.py](https://github.com/kuhl-haus/bedrock-access-gateway-cdk/blob/mainline/cdk/stacks/hosted_zone_stack.py))
* IAM Role for creating Route53 delegation records in the hosted zone parent account. ([r53_delegate_role_stack.py](https://github.com/kuhl-haus/bedrock-access-gateway-cdk/blob/mainline/cdk/stacks/r53_delegate_role_stack.py))
* ALB, Route53 DNS name for your API, & ACM vended TLS certificate ([load_balancer_stack.py](https://github.com/kuhl-haus/bedrock-access-gateway-cdk/blob/mainline/cdk/stacks/load_balancer_stack.py))
* Rest API: AWS Lambda, Lambda IAM role, Secrets Manager managed API key, KMS Customer-Managed Key ([rest_api_stack.py](https://github.com/kuhl-haus/bedrock-access-gateway-cdk/blob/mainline/cdk/stacks/rest_api_stack.py))

---

## Setup

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
python -m pip install -r requirements.txt --user
```


## Deploy the stacks

The CDK stacks and Docker image can be built and deployed on Windows or *nix-like environments.  

The bash and PowerShell scripts/instructions are provided here as best-effort to simplify building and deploying the stacks in your environment.  There are a myriad of reasons why these scripts may fail that has nothing to do with the code itself.  Therefore, I cannot help troubleshoot any problems or issues with deployment failures.

### PowerShell

Set `StackParameters` values.

I strongly recommend setting `AllowedCidr` to only allow trusted IP ranges.

```
$StackParameters = @{
    AllowedCidr="127.0.0.1/32";
    AwsAccountId="0123456789012";
    HostedZoneParentAccount="9876543210123";
    HostedZoneParentName="foo.com";
    HostedZoneName="bedrock.foo.com";
}
```

Deploy the Route 53 delegate role in the hosted zone parent account.
```
.\scripts\create-r53-delegate-role.ps1 @StackParameters
```

Deploy the Route 53 hosted zone and ECR repository in the deployment account.
```
.\scripts\deploy-dns-stack.ps1 @StackParameters

.\scripts\deploy-api-artifacts-stack.ps1 @StackParameters
```

Upload the Docker image to ECR

The PowerShell script is only in my cdk repository:
https://github.com/kuhl-haus/bedrock-access-gateway-cdk/blob/mainline/scripts/push-to-ecr.ps1

```
gh repo clone aws-samples/bedrock-access-gateway
cd .\bedrock-access-gateway\scripts\

Invoke-RestMethod -Uri https://raw.githubusercontent.com/kuhl-haus/bedrock-access-gateway-cdk/refs/heads/mainline/scripts/push-to-ecr.ps1 -Outfile .\push-to-ecr.ps1

cd ..\src
..\scripts\push-to-ecr.ps1

```


Deploy the Lambda and Load Balancer stacks:
```
.\scripts\deploy-api-handler-stack.ps1 @StackParameters

.\scripts\deploy-api-lb-stack.ps1 @StackParameters

```

### Bash

I strongly recommend setting AllowedCidr to only allow trusted IP ranges.

```
# Define parameters as environment variables
export AllowedCidr="127.0.0.1/32"
export AwsAccountId="0123456789012"
export HostedZoneParentAccount="9876543210123"
export HostedZoneParentName="foo.com"
export HostedZoneName="bedrock.foo.com"

```

Deploy the Route 53 delegate role in the hosted zone parent account.

```
./scripts/create-r53-delegate-role.sh \
    --allowed-cidr "${AllowedCidr}" \
    --aws-account-id "${AwsAccountId}" \
    --hosted-zone-parent-account "${HostedZoneParentAccount}" \
    --hosted-zone-parent-name "${HostedZoneParentName}" \
    --hosted-zone-name "${HostedZoneName}"
```

Deploy the Route 53 hosted zone and ECR repository in the deployment account.
```
./scripts/deploy-dns-stack.sh \
    --allowed-cidr "${AllowedCidr}" \
    --aws-account-id "${AwsAccountId}" \
    --hosted-zone-parent-account "${HostedZoneParentAccount}" \
    --hosted-zone-parent-name "${HostedZoneParentName}" \
    --hosted-zone-name "${HostedZoneName}"

./scripts/deploy-api-artifacts-stack.sh \
    --allowed-cidr "${AllowedCidr}" \
    --aws-account-id "${AwsAccountId}" \
    --hosted-zone-parent-account "${HostedZoneParentAccount}" \
    --hosted-zone-parent-name "${HostedZoneParentName}" \
    --hosted-zone-name "${HostedZoneName}"

```

Upload the Docker image to ECR

Bash script: https://github.com/aws-samples/bedrock-access-gateway/blob/main/scripts/push-to-ecr.sh

```
gh repo clone aws-samples/bedrock-access-gateway
cd bedrock-access-gateway/src
../scripts/push-to-ecr.sh
```


Deploy the Lambda and Load Balancer stacks:
```
./scripts/deploy-api-handler-stack.sh \
    --allowed-cidr "${AllowedCidr}" \
    --aws-account-id "${AwsAccountId}" \
    --hosted-zone-parent-account "${HostedZoneParentAccount}" \
    --hosted-zone-parent-name "${HostedZoneParentName}" \
    --hosted-zone-name "${HostedZoneName}"
    
./scripts/deploy-api-lb-stack.sh \
    --allowed-cidr "${AllowedCidr}" \
    --aws-account-id "${AwsAccountId}" \
    --hosted-zone-parent-account "${HostedZoneParentAccount}" \
    --hosted-zone-parent-name "${HostedZoneParentName}" \
    --hosted-zone-name "${HostedZoneName}"
    
```


## Test
```
curl https://proxy.bedrock.foo.com/health

```

# Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation


