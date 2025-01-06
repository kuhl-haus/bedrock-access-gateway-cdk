#!/bin/bash

set -exu

cdk ls || exit 1
cdk bootstrap || exit 1
cdk deploy --all --require-approval never --progress events || exit 1
