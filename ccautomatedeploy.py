import boto3

def lambda_handler(event, context):
    modifiedfiles = event['commits'][0]['modified']
    print("Modified files {0}".format(modifiedfiles) )
