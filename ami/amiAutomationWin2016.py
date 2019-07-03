import boto3

def lambda_handler(event, context):
    client = boto3.client('ssm')
    response = client.start_automation_execution(
    DocumentName='Win2016',
    DocumentVersion='5',
    Parameters={
        'SourceAmiId': [
            '{{ssm:latestAmiWin2016}}',
        ]
    }
)
