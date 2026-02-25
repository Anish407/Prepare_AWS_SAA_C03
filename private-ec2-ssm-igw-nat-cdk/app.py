#!/usr/bin/env python3
import os

import aws_cdk as cdk

from private_ec2_ssm_igw_nat_cdk.private_ec2_ssm_igw_nat_cdk_stack import PrivateEc2SsmIgwNatCdkStack
from private_ec2_ssm_igw_nat_cdk.route53stack import Route53Stack


app = cdk.App()

ENVIRONMENTS = {
    "dev": cdk.Environment(
        account="1234",
        region="us-east-1"
    ),
    "prod": cdk.Environment(
        account="1234",
        region="us-east-1"
    )
}

env= ENVIRONMENTS["dev"]

stack1=PrivateEc2SsmIgwNatCdkStack(app, "PrivateEc2SsmIgwNatCdkStack",
    env=env,
    )



stack2=Route53Stack(app, "Route53Stack",
                    vpc=stack1.vpc,
                    destinationIP=stack1.destination_instance.instance_private_ip,
                    env=env,
                    )

stack2.add_dependency(stack1)

app.synth()
