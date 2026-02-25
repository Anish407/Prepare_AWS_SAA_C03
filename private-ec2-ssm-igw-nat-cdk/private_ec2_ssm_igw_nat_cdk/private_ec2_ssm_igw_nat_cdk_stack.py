from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ssm as ssm,
    CfnOutput,
)
from constructs import Construct

from .constants import ParameterNames 

class PrivateEc2SsmIgwNatCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(self, "MyVpc",
                max_azs=1,
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
        
       
            #Create an IAM role for EC2 instances to access SSM
        sg = ec2.SecurityGroup(
            self,
            "PrivateInstanceSg",
            vpc=self.vpc,
            description="Private EC2 accessed only via SSM (no inbound rules)",
            allow_all_outbound=True,
        )
        sg2 = ec2.SecurityGroup(
            self,
            "destinationSg",
            vpc=self.vpc,
            description="destination EC2 security group",
            allow_all_outbound=True
        )
        sg2.add_ingress_rule(
            peer=sg,
            connection=ec2.Port.all_icmp(),
            description="Allow ICMP (ping) from source security group"
        )
        
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
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            role=role,
            security_group=sg,
            
        )
        # Create destination EC2 instance in private subnet
        self.destination_instance = ec2.Instance(
            self,
            "DestinationEc2",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.MachineImage.latest_amazon_linux2(),
            role=role,
            security_group=sg2,
            
        )

        CfnOutput(self, "Instance1Id", value=instance.instance_id)
        CfnOutput(self, "InstanceId1_privateIP", value=instance.instance_private_ip)

        CfnOutput(self, "DestinationInstanceId", value=self.destination_instance.instance_id)
        CfnOutput(self, "DestinationPrivateIp", value=self.destination_instance.instance_private_ip)