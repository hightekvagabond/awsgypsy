##############################
# This script was written to be a lambda
#
# If a GuardDuty Alerts a Finding this lambda is triggered and used as a gateway to other auto remediation lambdas
# 
# It accepts two enviroment Variables:
#    awsgypsybucket - name of the bucket to write logs of events so you can see details after the fact
#    snsarn - sns queue that receives notifications, you can subscribe email to this sns queue
#
# It also accepts a list of lambdas to invoke are a result of GD findings, the key is always the finding type with all non-alpha-numerics removed
# The value is the lambda name
#
###############################

from __future__ import print_function
import boto3
import os
import json
import re


myscriptname = 'GDFindings'

def lambda_handler(event, context):
    #print(json.dumps(event, indent=2))
    
    eventtype = event[0]['type']
    eventtype_key = re.sub(r'\W+', '', eventtype)
    
    print("Type: " + eventtype)
    print("Type_key: " + eventtype_key)
    
    if eventtype_key in os.environ.keys():
        print("Calling Function " + os.environ[eventtype_key])
        lambdaclient = boto3.client('lambda')
        response = lambdaclient.invoke(
            FunctionName=os.environ[eventtype_key],
            InvocationType='Event',
            #LogType='None',
            #ClientContext=json.dumps(event, indent=2)
            Payload=json.dumps(event)
            )
    else:
        if 'awsgypsybucket' in os.environ.keys():
           SaveToS3(os.environ['awsgypsybucket'],event['id'],json.dumps(event, indent=2))
        if 'snsarn' in os.environ.keys():
            PublishToSNS(os.environ['snsarn'],'Warning: GuardDuty Alerted for a Type we are not managing yet, it was type ' + eventtype + ' and the logs are stored at s3://' + os.environ['awsgypsybucket'] + '/Logs/CloudTrailWatcher/' + event['id'] + '.json')

    return 'Lambda'
