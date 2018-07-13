from __future__ import print_function
import awsgypsylib
from datetime import datetime
from datetime import timedelta
import boto3
import os

iam = boto3.client('iam')

expire = 90
if 'expire' in os.environ:
    expire = os.environ['expire']

#Dev Note: this function works to clean up keys, but does not write a report, and does not allow you to build a list of keys to exclude

##########################################
#
# This function walks through all users and checks their access keys age
# by default it expires keys after 90 days of non use, you can change this number by
# creating an enviroment variable called "expire"
#
##########################################

def lambda_handler(a,b):
    print("------checking users------")
    right_now = datetime.now().replace(tzinfo=None)
    for user in iam.list_users()['Users']:
        keys = iam.list_access_keys(UserName=user['UserName'])
        for key in keys['AccessKeyMetadata']:
            last_used = iam.get_access_key_last_used(AccessKeyId=key['AccessKeyId'])
            key_created = key['CreateDate']
            key_last_used_obj = last_used['AccessKeyLastUsed']
            if 'LastUsedDate' in key_last_used_obj:
                key_last_used = key_last_used_obj['LastUsedDate']
                days_since_used = right_now - key_last_used.replace(tzinfo=None)
            else:
                key_last_used = 'Never'
                days_since_used = timedelta(0)
            print("key " + key['AccessKeyId'] + " Created: " + str(key_created) + " And Last Used: " + str(key_last_used))
            #print(str(type(right_now)) + " " + str(type(key_created)) + " " + str(type(key_last_used)))
            key_age = right_now - key_created.replace(tzinfo=None)
            deleteit = False
            print("key is " + str(key_age.days) + " days old")
            if (str(key_last_used) == 'Never' and key_age.days > expire):
                print("delete this because it's more than " + str(expire) + " days old and has never been used")
                deleteit = True
            elif days_since_used.days > expire:
                print("delete because it hasn't been used for more than " + str(expire) + " days")
                deleteit = True
            if deleteit == True:
                response = iam.delete_access_key(UserName=user['UserName'], AccessKeyId=key['AccessKeyId'])
                print("Deleting " + str(key['AccessKeyId']) + " from user " + str(user['UserName']))
    print("------done checking users------")
    print("running unused_iam_credentials report")
