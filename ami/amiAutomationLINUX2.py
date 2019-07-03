import boto3

def lambda_handler(event, context):
    client = boto3.client('ssm')
    response = client.start_automation_execution(
    DocumentName='LINUX2',
    DocumentVersion='5',
    Parameters={
        'SourceAmiId': [
            '{{ssm:latestAMILINUX2}}',
        ]
    }
)
