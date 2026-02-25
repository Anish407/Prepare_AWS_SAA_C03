from aws_cdk import (
    CfnOutput,
    Stack,  aws_ec2 as ec2, aws_route53 as route53,
        aws_ssm as ssm,
)
from constructs import Construct
from .constants import ParameterNames

class Route53Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str,vpc: ec2.IVpc, destinationIP: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a Route 53 private hosted zone
        hosted_zone = route53.PrivateHostedZone(self, "MyPrivateHostedZone",
            zone_name="example.com",
            vpc=vpc
        )

        # Create a Route 53 A record in the private hosted zone
        route53.ARecord(self, "MyARecord",  
            zone=hosted_zone,
            record_name="internal.example.com",
            target=route53.RecordTarget.from_ip_addresses(destinationIP))
        
        CfnOutput(self, "HostedZoneId", value=hosted_zone.hosted_zone_id)