#!/usr/bin/python

import re
import os
import sys
import lxml
import boto3
import base64
import getpass
import logging
import requests
from pytz import timezone
from bs4 import BeautifulSoup
from datetime import datetime
from os.path import expanduser
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from configparser import ConfigParser

##########################################################################

#####################authetication and get list ########################################

####### username retention for future ################

def getoldusername():
    try:
        userfile = open(expanduser("~")+'\\username', 'r')
    except:
        userfile = open(expanduser("~")+'\\username', 'w+')
    ul = userfile.readlines()
    if len(ul) == 0:
        return 0
    else:
        return ul[0]

def saveusername(usrname):
    with open(expanduser("~")+'\\username', 'w+') as f:
        f.write(usrname)
        f.close()

#######################################################
###########username and password check ################

def getusername():
    prevdata = getoldusername()
    if prevdata == 0:
        print ('Username:',end=" ")
        name = str(input())
        if len(name) == 0:
            print ('Empty Username. Please type a valid Username')
            name = getusername()
        saveusername(name)
    else:
        print ('Found Username: {0}'.format(prevdata))
        print ('USE Y/N: y?',end=" ")
        inn = str(input())
        if inn.lower() == 'y' or inn.lower() == '':
            name = prevdata
        else:
            print ('Username:',end=" ")
            name = str(input())
            if len(name) == 0:
                print ('Empty Username. Please type a valid Username')
                name = getusername()
    return name

def getpassword():
    paswrd = getpass.getpass()
    if len(paswrd) == 0:
        print ('Empty Password. Please type a valid Password')
        paswrd = getpassword()
    return paswrd


##########################################
# Initiate session handler

def getassertion(idpentryurl,username,password):
    # Programmatically get the SAML assertion
    # Opens the initial IdP url and follows all of the HTTP302 redirects, and
    # gets the resulting login page
    session = requests.Session()
    formresponse = session.get(idpentryurl, verify=True)
    # Capture the idpauthformsubmiturl, which is the final url after all the 302s
    idpauthformsubmiturl = formresponse.url
    # Parse the response and extract all the necessary values
    # in order to build a dictionary of all of the form values the IdP expects
    formsoup = BeautifulSoup(formresponse.text,"lxml")
    payload = {}
    for inputtag in formsoup.find_all(re.compile('(INPUT|input)')):
        name = inputtag.get('name','')
        value = inputtag.get('value','')
        if "user" in name.lower():
            #Make an educated guess that this is the right field for the username
            payload[name] = username
        elif "email" in name.lower():
            #Some IdPs also label the username field as 'email'
            payload[name] = username
        elif "pass" in name.lower():
            #Make an educated guess that this is the right field for the password
            payload[name] = password
        else:
            #Simply populate the parameter with the existing value (picks up hidden fields in the login form)
            payload[name] = value
    # Set our AuthMethod to Form-based auth because the code above sees two values
    # for authMethod and the last one is wrong
    payload['AuthMethod'] = 'FormsAuthentication'
    # Debug the parameter payload if needed
    # Use with caution since this will print sensitive output to the screen
    # print payload
    # Some IdPs don't explicitly set a form action, but if one is set we should
    # build the idpauthformsubmiturl by combining the scheme and hostname
    # from the entry url with the form action target
    # If the action tag doesn't exist, we just stick with the
    # idpauthformsubmiturl above
    for inputtag in formsoup.find_all(re.compile('(FORM|form)')):
        action = inputtag.get('action')
        loginid = inputtag.get('id')
        if (action and loginid == "loginForm"):
            parsedurl = urlparse(idpentryurl)
            idpauthformsubmiturl = parsedurl.scheme + "://" + parsedurl.netloc + action

    # print idpauthformsubmiturl
    # print ''
    # Performs the submission of the IdP login form with the above post data
    loginresponse = session.post(
        idpauthformsubmiturl, data=payload, verify=True)
        # Debug the response if needed
    # print (loginresponse.text)
    # MFA Step 1 - If you have MFA Enabled, there are two additional steps to authenticate
    # Choose a verification option and reload the page
    # Capture the idpauthformsubmiturl, which is the final url after all the 302s
    mfaurl = loginresponse.url
    loginsoup = BeautifulSoup(loginresponse.text,"lxml")
    payload2 = {}
    for inputtag in loginsoup.find_all(re.compile('(INPUT|input)')):
        name = inputtag.get('name','')
        value = inputtag.get('value','')
        #Simply populate the parameter with the existing value (picks up hidden fields in the login form)
        payload2[name] = value
    ##############Giver User Verification option choice here ########################
    ############# Verification Code ##########
    lls = []
    mfall = []
    for mfaoption in loginsoup.find_all(re.compile('(a)')):
        lls.append(mfaoption)
    for data in lls:
        if data.name == 'a':
            mfall.append(data)
    if len(mfall) == 0:
        print ("Username and Password dont match records. Please try again")
        sys.exit()
    else:
        mfallf = []
        for data in mfall:
            if data.string is not None:
                mfallf.append(data)
        print ("Please choose an option for MFA Verification")
        print("Default choice is 1")
        k = 1
        for value in mfallf:
            try:
                if value.string.find('code') == -1:
                    print ('[{0}] {1}'.format(k,value.string))
            except:
                pass
            k = k+1
        print ("Your Choice:",end=" ")

    try:
        cho = int(input())-1
        if cho > len(mfallf) or cho < 0 :
            print ("Wrong input choosing default option 1")
            cho = 1
    except:
        print ("Wrong input choosing default option 1")
        cho = 1

    print ("Waiting for authentication......")
    print("")
    # '[1] verificationOption0 = mobile app authenticate'
    # "[2] verificationOption1 = phone call"
    # "[3] verificationOption2 = smss"
    # "[4] verificationOption3 = mobile app code"
    ###change to input
    verificationOption = 'verificationOption'+str(cho)
    #############################################################################
    # Set mfa auth type here...
    payload2['__EVENTTARGET'] = verificationOption
    payload2['AuthMethod'] = 'AzureMfaServerAuthentication' ### can change with mfa server can be radius etc
    mfaresponse = session.post(
        mfaurl, data=payload2, verify=True)
    # Debug the response if needed
    # print (mfaresponse.text)
    # MFA Step 2 - Fire the form and wait for verification
    mfasoup = BeautifulSoup(mfaresponse.text,"lxml")
    payload3 = {}
    for inputtag in mfasoup.find_all(re.compile('(INPUT|input)')):
        name = inputtag.get('name','')
        value = inputtag.get('value','')
        #Simply populate the parameter with the existing value (picks up hidden fields in the login form)
        payload3[name] = value
    payload3['AuthMethod'] = 'AzureMfaServerAuthentication'
    mfaresponse2 = session.post(
        mfaurl, data=payload3, verify=True)
    # # Decode the response and extract the SAML assertion
    soup = BeautifulSoup(mfaresponse2.text,'lxml')
    assertion = ''
    # Look for the SAMLResponse attribute of the input tag (determined by
    # analyzing the debug print lines above)
    for inputtag in soup.find_all('input'):
        if(inputtag.get('name') == 'SAMLResponse'):
            # (inputtag.get('value'))
            assertion = inputtag.get('value')
    # Better error handling is required for production use.
    if (assertion == ''):
        #TODO: Insert valid error checking/handling
        print ('Authentication Failed, Please try again')
        sys.exit(0)
    return assertion
    # Debug only
    # print(base64.b64decode(assertion))

def getalltokens(awsroles,filename):
    # Variables
        # region: The default AWS region that this script will connect
    # to for all API calls
    region = 'us-east-1'
    # output format: The AWS CLI output format that will be configured in the
    # saml profile (affects subsequent CLI calls)
    outputformat = 'json'
    # # Read in the existing config file
    config = ConfigParser()
    config.read(filename)
    i = 0
    for awsrole in awsroles:
        if i < len(awsroles):
            role_arn = awsroles[int(i)].split(',')[0]
            principal_arn = awsroles[int(i)].split(',')[1]
            acctname = awsrole.split(',')[0].split(':')[4]+'-'+awsrole.split(',')[0].split(':')[5].split('/')[1]
            client = boto3.client('sts')
            try:
                token = client.assume_role_with_saml(RoleArn=role_arn, PrincipalArn=principal_arn, SAMLAssertion=assertion)
                # Write the AWS STS token into the AWS credential file
                #print (token)
                access_key = token['Credentials']['AccessKeyId']
                secret_key = token['Credentials']['SecretAccessKey']
                session_token= token['Credentials']['SessionToken']
                expiration = token['Credentials']['Expiration']
                # Put the credentials into a saml specific section instead of clobbering
                # the default credentials
                if not config.has_section(acctname):
                    config.add_section(acctname)
                config.set(acctname, 'output', outputformat)
                config.set(acctname, 'region', region)
                config.set(acctname, 'aws_access_key_id', access_key)
                config.set(acctname, 'aws_secret_access_key', secret_key)
                config.set(acctname, 'aws_session_token', session_token)
            except:
                print ("Unable to retrieve tokens for account {0} IAM role/account doesn't exist.".format(acctname))
                pass #continue
            i = i+1
    #Write the updated config file
    with open(filename, 'w+') as configfile:
        config.write(configfile)
    return filename,expiration

###### Get a single account token ###########

def getaccounttoken(awsroles,selectedroleindex,filename):
    # Variables
    # region: The default AWS region that this script will connect
    # to for all API calls
    region = 'us-east-1'
    # output format: The AWS CLI output format that will be configured in the
    # saml profile (affects subsequent CLI calls)
    outputformat = 'json'
    config = ConfigParser()
    config.read(filename)
    role_arn = awsroles[int(selectedroleindex)].split(',')[0]
    principal_arn = awsroles[int(selectedroleindex)].split(',')[1]
    acctname = awsroles[int(selectedroleindex)].split(',')[0].split(':')[4]+'-'+awsroles[int(selectedroleindex)].split(',')[0].split(':')[5].split('/')[1]
    client = boto3.client('sts')
    try:
        token = client.assume_role_with_saml(RoleArn=role_arn, PrincipalArn=principal_arn, SAMLAssertion=assertion)
        # Write the AWS STS token into the AWS credential file
        #print (token)
        access_key = token['Credentials']['AccessKeyId']
        secret_key = token['Credentials']['SecretAccessKey']
        session_token= token['Credentials']['SessionToken']
        expiration = token['Credentials']['Expiration']
        # Put the credentials into a saml specific section instead of clobbering
        # the default credentials
        if not config.has_section(acctname):
            config.add_section(acctname)
            config.set(acctname, 'output', outputformat)
            config.set(acctname, 'region', region)
            config.set(acctname, 'aws_access_key_id', access_key)
            config.set(acctname, 'aws_secret_access_key', secret_key)
            config.set(acctname, 'aws_session_token', session_token)
    except:
            print ("Unable to retrieve tokens for account {0} IAM role/account doesn't exist.".format(acctname))
    #Write the updated config file
    with open(filename, 'w+') as configfile:
        config.write(configfile)
    return filename,expiration,acctname
#######################################################

def getawsroles(assertion):
    # Parse the returned assertion and extract the authorized roles
    awsroles = []
    root = ET.fromstring(base64.b64decode(assertion))
    for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
        if (saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'):
            for saml2attributevalue in saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
                awsroles.append(saml2attributevalue.text)

    # Note the format of the attribute value should be role_arn,principal_arn
    # but aws docs list it as principal_arn,role_arn so let's reverse
    # them if needed
        for awsrole in awsroles:
            chunks = awsrole.split(',')
            if'saml-provider' in chunks[0]:
                newawsrole = chunks[1] + ',' + chunks[0]
                index = awsroles.index(awsrole)
                awsroles.insert(index, newawsrole)
                awsroles.remove(awsrole)
    # awsconfigfile: The file where this script will store the temp
    # credentials under the saml profile
    awsconfigfile = '\.aws\credentials'
    filename = expanduser("~") + awsconfigfile
    awsdir = expanduser("~")+'\\.aws'
    if not os.path.exists(awsdir):
        os.makedirs(awsdir)
    ###############################################################################
    ############################## Set Proxy ######################

    if "HTTPS_PROXY" in os.environ:
        print ("Proxy has already been set")
        print ("")
    else:
        print("Setting Proxy")
        os.environ["HTTP_PROXY"] = "http://username:password@corp-eq5-proxy.mhc:8080"
        os.environ["HTTPS_PROXY"] = "https://username:password@corp-eq5-proxy.mhc:8080"

    ###################################################################################
    # Overwrite and delete the credential variables,  for safety

    # username = '##############################################'
    # password = '##############################################'
    # del username
    # del password

    ############################################################################
    ############ AWS API CALLS ################################################

    ########## Get all accounts tokens ###########
    #################User choice #############################
    # If user has more than one role, ask the user which one they want,
    # otherwise just proceed
    print ("")
    if len(awsroles) > 1:
        i = 0
        print ("Please choose the role you would like to assume:")
        for awsrole in awsroles:
            print ('[', i+1, ']: ',awsrole.split(',')[0].split(':')[4]+'-'+awsrole.split(',')[0].split(':')[5].split('/')[1])
            i += 1
        print ('[', i+1, ']: Default all accounts')
        print("")
        print ("SELECTION: ",end=" ")
        selectedroleindex = input()
        try:
            selectedroleindex = int(selectedroleindex)-1
        except:
            print ('You selected an invalid role index, Selecting default that is all roles')
            selectedroleindex = len(awsroles)
        # Basic sanity check of input
        if selectedroleindex > len(awsroles) or selectedroleindex < 0:
            print ('You selected an invalid role index, Selecting default that is all roles')
            selectedroleindex = len(awsroles)
    else:
        print ("Only one role found:",awsrole.split(',')[0].split(':')[4]+'-'+awsrole.split(',')[0].split(':')[5].split('/')[1])
        selectedroleindex = 0

    ####################################################

    if selectedroleindex == len(awsroles):
        fname,expiration = getalltokens(awsroles,filename)
        acctname = 'Multiple Accounts'
    else:
        fname,expiration,acctname = getaccounttoken(awsroles,selectedroleindex,filename)

    exp_est = expiration.astimezone(timezone('US/Eastern'))
    # Give the user some basic info as to what has just happened

    print ('\n\n----------------------------------------------------------------')
    print ('Your new access key pair has been stored in the AWS configuration file {0} under the profile {1}.'.format(fname,acctname))
    print("")
    print ('NOTE that tokens will EXPIRE at EST {0}.'.format(exp_est))
    print("")
    print ('After this time, you may safely rerun this script to refresh your access key pair.')
    print ('To use this credential, call the AWS CLI with the --profile option (e.g. aws --profile default ec2 describe-instances).')
    print ('----------------------------------------------------------------\n\n')

    input("Press enter to exit")
#########################################################
#### Main Execution ######

# idpentryurl: The initial url that starts the authentication process.
idpentryurl = 'https://fs.spglobal.com/adfs/ls/IdpInitiatedSignOn.aspx?loginToRp=urn:amazon:webservices'
# Uncomment to enable low level debugging
# logging.basicConfig(level=logging.DEBUG)

# Get the federated credentials from the user
username = getusername()
password = getpassword()
print ('')
#getawsroles(getassertion(idpentryurl,username,password))
#assertion = getassertion(idpentryurl,True,username,password)
#getawsroles(assertion)

##################### END ###########################
