from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2  as elbv2,
    aws_logs as logs,
)
from aws_cdk import aws_elasticloadbalancingv2 as elbv2

from constructs import Construct


class EcsStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        listener: elbv2.IApplicationListener,
        alb_security_group: ec2.ISecurityGroup,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repo = ecr.Repository.from_repository_name(
            self,
            "ImportedRepo",
            "my-web-repo",
        )

        cluster = ecs.Cluster(
            self,
            "WebCluster",
            vpc=vpc,
        )

        ecs_security_group = ec2.SecurityGroup(
            self,
            "EcsServiceSecurityGroup",
            vpc=vpc,
            description="Allow HTTP from the ALB to ECS tasks",
            allow_all_outbound=True,
        )

        ecs_security_group.add_ingress_rule(
            peer=alb_security_group,
            connection=ec2.Port.tcp(80),
            description="Allow HTTP from ALB",
        )

        task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            cpu=256,
            memory_limit_mib=512,
        )

        log_group = logs.LogGroup(
            self,
            "WebLogGroup",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        container = task_definition.add_container(
            "WebContainer",
            image=ecs.ContainerImage.from_ecr_repository(repo, tag="v1"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="web",
                log_group=log_group,
            ),
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=80)
        )

        service = ecs.FargateService(
            self,
            "WebService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            assign_public_ip=False,
            security_groups=[ecs_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
        )

        listener.add_targets(
            "EcsTargets",
            port=80,
            targets=[service],
            health_check=elbv2.HealthCheck(
                path="/",
                healthy_http_codes="200",
            ),
        )

        CfnOutput(self, "ClusterName", value=cluster.cluster_name)
        CfnOutput(self, "ServiceName", value=service.service_name)
        CfnOutput(self, "RepositoryName", value=repo.repository_name)
