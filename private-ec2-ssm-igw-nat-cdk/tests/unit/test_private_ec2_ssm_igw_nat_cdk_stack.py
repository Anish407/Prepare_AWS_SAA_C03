import aws_cdk as core
import aws_cdk.assertions as assertions

from private_ec2_ssm_igw_nat_cdk.private_ec2_ssm_igw_nat_cdk_stack import PrivateEc2SsmIgwNatCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in private_ec2_ssm_igw_nat_cdk/private_ec2_ssm_igw_nat_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = PrivateEc2SsmIgwNatCdkStack(app, "private-ec2-ssm-igw-nat-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
