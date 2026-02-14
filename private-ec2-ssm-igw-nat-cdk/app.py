#!/usr/bin/env python3
import os

import aws_cdk as cdk

from private_ec2_ssm_igw_nat_cdk.private_ec2_ssm_igw_nat_cdk_stack import PrivateEc2SsmIgwNatCdkStack


app = cdk.App()
PrivateEc2SsmIgwNatCdkStack(app, "PrivateEc2SsmIgwNatCdkStack",
    env=cdk.Environment(account='1234', region='us-east-1'),
    )

app.synth()
