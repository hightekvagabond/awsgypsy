##############################
# This script was written to be a lambda
#
# If a GuardDuty Alerts that a Malicious IP is Port Scanning an IP it blocks that IP
# 
# It accepts two enviroment Variables:
#    awsgypsybucket - name of the bucket to write logs of events so you can see details after the fact
#    snsarn - sns queue that receives notifications, you can subscribe email to this sns queue
#    ownertag - this is the name of the tag to look for on a resource that defines the owner's email address (optional: assume "owner")
#    
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
    print("Instance id: " + instanceid)
    
    #gather a list of offending ips
    badguyips = []
    for badguy in event[0]['service']['action']['portProbeAction']['portProbeDetails']:
        badguyips.append(badguy['remoteIpDetails']['ipAddressV4'])
    
    print("My badguys are " + str(badguyips))
    
    

    vpcs = []
    for interface in event[0]['resource']['instanceDetails']['networkInterfaces']:
        if interface['vpcId'] not in vpcs:
            vpcs.append(interface['vpcId'])

    
    print("vpcs: " + str(vpcs))    


    
    
    #add the bad guy ips to all the VCP ACLs
    s = boto3.Session(region_name='us-west-1')
    ec2res = s.resource('ec2')
    ec2c = s.client('ec2')
    #print(json.dumps(ec2c.describe_network_acls(), indent=2))
    
    acl_network = ec2c.describe_network_acls()
    acls = acl_network['NetworkAcls']
    managedacls = []
    for acl in acls:
        #print("-------------------------")
        #print(json.dumps(acl,indent=2))
        #print("-------------------------")
        rulenums = []
        thisrulenum = 400 #arbitrary number
        for rule in acl['Entries']:
            if rule['Egress'] == False: #only care about ingress rules
                rulenums.append(rule['RuleNumber'])
        for assoc in acl['Associations']:
            aclid = assoc['NetworkAclId']
            print("------" + aclid + "------")
            if aclid not in managedacls:
                managedacls.append(aclid)
                for badguyip in badguyips:
                    print("add blocking for " + badguyip + " to " + aclid)
                    while thisrulenum in rulenums:
                        thisrulenum = thisrulenum + 1
                    rulenums.append(thisrulenum)
                    response = ec2c.create_network_acl_entry( CidrBlock=badguyip + "/32", DryRun=False, Egress=False, IcmpTypeCode={'Code': 123,'Type': 123}, NetworkAclId=aclid, PortRange={'From': 0,'To': 65535 }, Protocol='-1', RuleAction='deny', RuleNumber=thisrulenum )
                        #Ipv6CidrBlock='string', #TODO: ipv6
    
    #TODO: check for owner tag and message them as well
    
    #if 'awsgypsybucket' in os.environ.keys():
    #    SaveToS3(os.environ['awsgypsybucket'],event[0]['id'],json.dumps(event, indent=2))
    #    
    if 'snsarn' in os.environ.keys():
        PublishToSNS(os.environ['snsarn'],'Warning: ' + event[0]['description'] + " Blocked " + ",".join(badguyips) + " in acls " + ",".join(managedacls))

    return 'Lambda'

####Include: lib/AllLambdaFunctions.py
