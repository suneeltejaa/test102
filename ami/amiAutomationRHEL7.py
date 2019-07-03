import boto3

def lambda_handler(event, context):
    client = boto3.client('ssm')
    response = client.start_automation_execution(
    DocumentName='RHEL7',
    DocumentVersion='5',
    Parameters={
        'SourceAmiId': [
            '{{ssm:latestAMIRHEL7}}',
        ]
    }
)
