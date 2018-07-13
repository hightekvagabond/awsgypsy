NOTE: This was a fail, you block ips at the VPC's ACL not at the security group, I was barking up the wrong tree, just saving this because there is some interesting code in here I might find a use for later



##############################
# This script was written to be a lambda
#
# If a GuardDuty Alerts that a Malicious IP is Port Scanning an IP it blocks that IP
# 
# It accepts two enviroment Variables:
#    awsgypsybucket - name of the bucket to write logs of events so you can see details after the fact
#    snsarn - sns queue that receives notifications, you can subscribe email to this sns queue
#    ownertag - this is the name of the tag to look for on a resource that defines the owner's email address (optional: assume "owner")
#    maliciousipsecgroup - name of the security group used to track Malicious IPs to be blocked (optional: assume awsgypsyBadGuys)
#
###############################

from __future__ import print_function
import boto3
import os
import json


myscriptname = 'GDEC2Portscan'

def lambda_handler(event, context):
    #print(json.dumps(event, indent=2))
    
    #figure out what we are calling the security groups
    maliciousipsecgroup = 'awsgypsyBadGuys'
    if 'maliciousipsecgroup' in os.environ.keys():
        maliciousipsecgroup = os.environ['maliciousipsecgroup']
    
    #get some info about this instance
    instanceid = event[0]['resource']['instanceDetails']['instanceId']
    region = event[0]['region']
    account = event[0]['accountId']
    print("Instance id: " + instanceid)
    
    #gather a list of offending ips
    badguyips = []
    for badguy in event[0]['service']['action']['portProbeAction']['portProbeDetails']:
        badguyips.append(badguy['remoteIpDetails']['ipAddressV4'])
    
    print("My badguys are " + str(badguyips))
    
    
    #find out if we already have the group for blocking malicious ips attached to the instance
    maliciousipsecgroup_attached = False
    maliciousipsecgroups = {}
    secgroups = []
    vpcs = []
    for interface in event[0]['resource']['instanceDetails']['networkInterfaces']:
        if interface['vpcId'] not in vpcs:
            vpcs.append(interface['vpcId'])
            newgroup = maliciousipsecgroup + "-" + str(interface['vpcId'])
            if newgroup not in maliciousipsecgroups.keys():
                maliciousipsecgroups[newgroup] = interface['vpcId']
                
    print('maliciousipsecgroups: ' + str(maliciousipsecgroups))
    
    for interface in event[0]['resource']['instanceDetails']['networkInterfaces']:
        for group in interface['securityGroups']:
            secgroups.append(group)
            if group['groupName'] in maliciousipsecgroups:
                maliciousipsecgroup_attached = True
    
    print("vpcs: " + str(vpcs))    
    print("secgroups: " + str(secgroups))
    print("Already Attached to the maliciousipgroup?: " + str(maliciousipsecgroup_attached) )
    
    
    #get the id for the groups that already exists
    maliciousipsecgroup_ids = {}
    if maliciousipsecgroup_attached != True:
        print('checking for existence of group ' + maliciousipsecgroup)
        ec2client = boto3.client('ec2')
        desc =  ec2client.describe_security_groups()
        maliciousipsecgroup_id = ''
        for group in desc['SecurityGroups']:
            print(group['GroupName'] + ":" + group['GroupId'])
            if group['GroupName'] in maliciousipsecgroups.keys():
                maliciousipsecgroup_ids[maliciousipsecgroups[group['GroupName']]] = group['GroupId'] #store the id of the group with a key of vpc
                
        for vpc in vpcs:
            if vpc not in maliciousipsecgroup_ids.keys():
                print(maliciousipsecgroup + "-" + vpc + " does not exist, we need to create it")
                #security_group = ec2.SecurityGroup('id')
                #for groupname in maliciousipsecgroups.keys():
                #print('make a group named ' + groupname + ' in vpc ' + maliciousipsecgroups[groupname])
                response = ec2client.create_security_group( Description='SecurityGroup Created to hold known Malicious IP addrresses that have probed our machines', GroupName=maliciousipsecgroup + "-" + vpc, VpcId=vpc, DryRun=False )
                print(str(response))
                maliciousipsecgroup_ids[vpc] = response['GroupId']
        else:
            print(maliciousipsecgroup + " exists we will use id " + maliciousipsecgroup_id)
        
    
    #add the bad guy ips to all the groups
    
    #add the appropriate groups to the interfaces
    
    
    
    #if 'awsgypsybucket' in os.environ.keys():
    #    SaveToS3(os.environ['awsgypsybucket'],event[0]['id'],json.dumps(event, indent=2))
    #    
    #if 'snsarn' in os.environ.keys():
    #    PublishToSNS(os.environ['snsarn'],'Warning: ' + event[0]['description'])

    return 'Lambda'

####Include: lib/AllLambdaFunctions.py
