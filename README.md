
# bedrock-access-gateway-cdk

Example CDK to accompany my fork of aws-samples/bedrock-access-gateway at [kuhl-haus/bedrock-access-gateway/tree/oldschool-engineer](https://github.com/kuhl-haus/bedrock-access-gateway/tree/oldschool-engineer).


---

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

**VERY IMPORTANT** - Replace the example default values in `app.py` for the following environment variables:
* HOSTED_ZONE_PARENT_ACCOUNT
* HOSTED_ZONE_PARENT_NAME
* AWS_ACCOUNT_ID
* HOSTED_ZONE_NAME

You will need to create a role in the Hosted Zone Parent Account with the following naming convention: `r53_${HOSTED_ZONE_PARENT_NAME}_${AWS_ACCOUNT_ID}`

**Permissions**
Replace `HOSTED_ZONE_PARENT_ID` with the hosted zone ID that will delegate to the deployment account.
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "route53:GetHostedZone",
                "route53:ChangeResourceRecordSets",
                "route53:ListResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/HOSTED_ZONE_PARENT_ID"
            ]
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "route53:TestDNSAnswer",
                "route53:ListHostedZones",
                "route53:GetHostedZoneCount",
                "route53:ListHostedZonesByName"
            ],
            "Resource": "*"
        }
    ]
}

```

**Trust Relationships**

Replace `AWS_ACCOUNT_ID` with the account ID where the Lambda will be deployed.
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::AWS_ACCOUNT_ID:root"
            },
            "Action": "sts:AssumeRole",
            "Condition": {}
        }
    ]
}
```

While not required, I strongly recommend setting `ALLOWED_CIDR` to only allow trusted IP ranges.


Synthesize the CDK definition files.
```
cdk synth
```

List stacks:
```
cdk ls
```

Bootstrap the stacks
```
cdk bootstrap 
```

Deploy all the stacks
```
cdk deploy --all --require-approval never --progress events
```

Deploy each stack individually
```
cdk deploy dns-stack --require-approval never --progress events
cdk deploy api-artifacts --require-approval never --progress events
cdk deploy api-handler --require-approval never --progress events
cdk deploy api-lb --require-approval never --progress events

```


## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation


