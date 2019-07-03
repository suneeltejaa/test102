# This script copies the AMI to other region and add tag 'DeleteOnCopy' with retention days specified.
import boto3
from dateutil import parser
import datetime
import collections

# Set the global variables
globalVars  = dict()
globalVars['Owner']                 = 'patrick_horrigan'
globalVars['Environment']           = 'Test'
globalVars['SourceRegion']          = 'us-east-1'
globalVars['destRegions']           = ['us-west-2','eu-west-1','ap-southeast-1']        # List of AWS Regions to which the AMI to be copied
globalVars['amiRetentionDays']      = int(5)                # AMI Rentention days in DR/Destination Region.

# Create the Boto Resources and Clients
srcEC2Resource  = boto3.resource('ec2', region_name = globalVars['SourceRegion'])

# Get the Account ID of the Lambda Runner Account - Assuming this is the source account
globalVars['awsAccountId']          = boto3.client('sts').get_caller_identity()['Account']

def img_replicator():

    # Get the list of images in source Region
    images = srcEC2Resource.images.filter(Owners=[ globalVars['awsAccountId'] ])

    to_tag = collections.defaultdict(list)

    imgReplicationStatus = {'Images': []}

    for image in images:
        image_date = parser.parse(image.creation_date)

        # Copy ONLY today's images
        if image_date.date() == (datetime.datetime.today()).date():

        # To Copy previous day images
        # if image_date.date() == (datetime.datetime.today()-datetime.timedelta(1)).date():

            # Copy to Multiple destinations
            for awsRegion in globalVars['destRegions']:

                destEC2Client = boto3.client('ec2', region_name=awsRegion)

                # Copy ONLY if the destination doesn't have an image already with the same name
                # AMI Names have to be UNIQUE
                if not destEC2Client.describe_images(Owners=[ globalVars['awsAccountId'] ], Filters=[{'Name':'name', 'Values':[image.name]}])['Images']:

                    print "Copying Image. \nImage Name:{name} \nID:{id} \nRegion:'{dest}'".format(name=image.name,id=image.id, dest=awsRegion)

                    new_ami = destEC2Client.copy_image(
                        DryRun=False,
                        SourceRegion=globalVars['SourceRegion'],
                        SourceImageId=image.id,
                        Name=image.name,
                        Description=image.description
                    )

                else:
                    print "Image {name} - {id} already present in Virginia Region".format( name=image.name, id=image.id )
                    imgReplicationStatus['Images'].append({'AMI-Id':image.id,'Status':'Already Exists'})


        else:
            print "There are no new images. The Image: {name} with AMI ID: {id} was created on {date}".format(name=image.name, id=image.id, date=image_date.strftime('%d-%m-%Y'))

    return imgReplicationStatus


def lambda_handler(event, context):
    img_replicator()

if __name__ == '__main__':
    lambda_handler(None, None)
