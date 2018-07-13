##############################
# This script was written to be a lambda
#
# If a cloudtrail is turned off this lambda turns it back on
# 
# It accepts two enviroment Variables:
#    awsgypsybucket - name of the bucket to write logs of events so you can see details after the fact
#    snsarn - sns queue that receives notifications, you can subscribe email to this sns queue
#
###############################

from __future__ import print_function
import boto3
import os
import json

myscriptname = 'WatchCloudTrail'

def lambda_handler(event, context):
    jobId = event['id']
    print("jobId: " + jobId)
    EventName = event['detail']['eventName']
    print("Event: " + EventName)
    TrailName = event['detail']['requestParameters']['name']
    print('TrailName:' + TrailName)
    
    if EventName == 'StopLogging':
        print('turning the trail back on')
        TrailClient = boto3.client('cloudtrail')
        response = TrailClient.start_logging(Name=TrailName)
    
    if 'awsgypsybucket' in os.environ.keys():
        SaveToS3(os.environ['awsgypsybucket'],event['id'],json.dumps(event, indent=2))
        
    if 'snsarn' in os.environ.keys():
        PublishToSNS(os.environ['snsarn'],'Warning: Watched Cloudtrail ' + TrailName + ':' + EventName + ' see logs at s3://' + os.environ['awsgypsybucket'] + '/Logs/CloudTrailWatcher/' + event['id'] + '.json')
    return 'lambda'

####Include: lib/AllLambdaFunctions.py
