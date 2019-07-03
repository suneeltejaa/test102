import boto3

def lambda_handler(event, context):
    client = boto3.client('ssm')
    response = client.start_automation_execution(
    DocumentName='Win2012R2-64bit',
    DocumentVersion='5',
    Parameters={
        'sourceAMIid': [
            '{{ssm:latestAmiWin2012}}',
        ]
    }
)