import boto3

def getParameter(event, context):
    client = boto3.client('ssm')
    response = client.get_parameters(
        Names=[
            'latestAmiWin2016',
        ],
        WithDecryption=False
    )
    credentials = response['Parameters'][0]['Value']
    return credentials

def lambda_handler(event, context):
    TARGET_ACCOUNT_ID = event['accountID']
    source_ec2 = boto3.resource('ec2')
    aminame = getParameter(event, context)
    source_ami = source_ec2.Image(aminame)
    source_snapshot = source_ec2.Snapshot(source_ami.block_device_mappings[0]['Ebs']['SnapshotId'])
    source_sharing = source_snapshot.describe_attribute(Attribute='createVolumePermission')
    print("Sharing %s with target account %s" % (aminame, TARGET_ACCOUNT_ID) )
    source_snapshot.modify_attribute(
        Attribute='createVolumePermission',
        OperationType='add',
        UserIds=[TARGET_ACCOUNT_ID]
        )
    source_ami.modify_attribute(
        LaunchPermission={
            'Add': [
                {
                    'UserId': TARGET_ACCOUNT_ID
                }
            ]
            }
        )
