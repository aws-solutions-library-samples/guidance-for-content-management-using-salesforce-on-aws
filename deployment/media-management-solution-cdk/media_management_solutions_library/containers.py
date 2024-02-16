# import aws_cdk
from aws_cdk import (
    aws_imagebuilder as imagebuilder,
    aws_ecr as ecr,
    aws_iam as iam,
    Aws

)
from constructs import Construct


class ContainerRecipeStack(Construct):
    def __init__ (self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Create 3 ECR repos
        self.instance_profile_role = iam.Role(self, "MyRole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        self.instance_profile_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        self.instance_profile_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("EC2InstanceProfileForImageBuilderECRContainerBuilds"))
        self.instance_profile = iam.InstanceProfile(self, id="MyInstanceProfile", role=self.instance_profile_role)
        self.image_config = imagebuilder.CfnInfrastructureConfiguration(self, id=f"InfrastructureConfiguration{construct_id}",
                                                                        name=f"InfrastructureConfiguration{construct_id}",
                                                                        instance_profile_name=self.instance_profile.instance_profile_name)

    def create_container_recipe (self, name, parent_image, component_arn, target_repository,
                                 dockerfile_template_data, version):
        cfn_container_recipe_props = imagebuilder.CfnContainerRecipeProps(
            components=[imagebuilder.CfnContainerRecipe.ComponentConfigurationProperty(
                component_arn=component_arn,
            )],
            container_type="DOCKER",
            name=name,
            parent_image=parent_image,
            target_repository=imagebuilder.CfnContainerRecipe.TargetContainerRepositoryProperty(
                repository_name=target_repository, service='ECR'
            ),
            version=version
        )
        return imagebuilder.CfnContainerRecipe(self, name,
                                               components=cfn_container_recipe_props.components,
                                               container_type=cfn_container_recipe_props.container_type,
                                               name=cfn_container_recipe_props.name,
                                               parent_image=cfn_container_recipe_props.parent_image,
                                               target_repository=cfn_container_recipe_props.target_repository,
                                               dockerfile_template_data=dockerfile_template_data,
                                               version=cfn_container_recipe_props.version
                                               )

    def container_image_create (self, ecr_repo_name: str, dockerfile_template_data: str, container_recipe_name) ->dict:
        ecr_repo = ecr.Repository(self, ecr_repo_name,
                                  repository_name=ecr_repo_name,
                                  image_scan_on_push=True,
                                  image_tag_mutability=ecr.TagMutability.IMMUTABLE)
        container_recipe = self.create_container_recipe(name=container_recipe_name,
                                                        parent_image=f"arn:{Aws.PARTITION}:imagebuilder:{Aws.REGION}:aws:image/amazon-linux-x86-2/x.x.x",
                                                        component_arn=f"arn:{Aws.PARTITION}:imagebuilder:{Aws.REGION}:aws:component/python-3-linux/x.x.x",
                                                        target_repository=ecr_repo.repository_name,
                                                        dockerfile_template_data=dockerfile_template_data,
                                                        version="1.0.0")
        container_image = imagebuilder.CfnImage(self, id=f"{container_recipe_name}-image",
                                                container_recipe_arn=container_recipe.attr_arn,
                                                infrastructure_configuration_arn=self.image_config.attr_arn)

        return {'repo': ecr_repo, 'image': container_image}
