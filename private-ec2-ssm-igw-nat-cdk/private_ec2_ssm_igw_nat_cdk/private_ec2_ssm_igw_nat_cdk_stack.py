from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_iam as iam, 
    # aws_sqs as sqs,
)
from constructs import Construct

class PrivateEc2SsmIgwNatCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC with public and private subnets
        vpc = ec2.Vpc(self, "MyVpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        sg= ec2.SecurityGroup(self,
                               "ec2-sg",
                               vpc=vpc,
                               allow_all_outbound=True,
                               description="Private EC2 accessed only via SSM (no inbound rules)")
        
        role = iam.Role(self, "ec2-smm",
                        assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
                        managed_policies=[
                            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
                        ]
        )
        # Create EC2 instance in private subnet
        instance = ec2.Instance(
            self,
            "PrivateEc2",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            role=role,
            security_group=sg,
        )

        CfnOutput(self, "InstanceId", value=instance.instance_id)
        CfnOutput(self, "PrivateIp", value=instance.instance_private_ip)