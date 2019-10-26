# -*- coding: utf-8 -*-

# This is a simple Hello World Alexa Skill, built using
# the implementation of handler classes approach in skill builder.
import logging
import boto3
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# lambda environment variable
bucket =  os.environ['Bucket'] 

# memory dump filename
raw_file = "windows-memory.raw"

def handle(event, context):
    # type: (HandlerInput) -> Response
    """
    This function will download a memory dump exe from S3,
    run it, and upload the dump to S3; ready for your awesome 
    forensics skills.
    """
    ec2 = boto3.resource('ec2', region_name='us-east-2')
    ssm_client = boto3.client('ssm')
    
    target = event["target"].value

    host_list = [instance.id for instance in ec2.instances.all() for name in instance.tags if name["Key"] == "Name" if name["Value"].lower() == target.lower()]
    if len(host_list) > 0:
        for hosts in host_list:
            ec2_instance = ec2.Instance(hosts)
            platform = ec2_instance.platform
            state = ec2_instance.state['Name']
            if state == "running":
                instance_ids = [hosts]
                if platform == "windows":
                    commands = [f"aws s3 cp s3://{bucket}/tools/winpmem_1.6.2.exe C:\\Windows\\Temp", 
                    "cd C:\\Windows\\Temp", 
                    f".\winpmem_1.6.2.exe {raw_file}", 
                    f"aws s3 cp {raw_file} s3://{bucket}/evidence/"]
                    resp = ssm_client.send_command(DocumentName="AWS-RunPowerShellScript", Parameters={'commands': commands}, InstanceIds=instance_ids)
                else:
                    logger.error("ERROR: platform is not Windows")
            else:
                logger.error("ERROR: target instance is inactive")
    else:
        logger.error("ERROR: no acceptable hosts provided")