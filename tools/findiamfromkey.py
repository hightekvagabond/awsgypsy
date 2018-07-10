#!/usr/bin/python


# Find the IAM username belonging to the TARGET_ACCESS_KEY
# Useful for finding IAM user corresponding to a compromised AWS credential

# Requirements:
#
# Environmental variables: 
# 		AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# python: 
#		boto


#currently uses your default profile so, you need to change that if it's not the profile you are using

import sys
import pprint
pp = pprint.PrettyPrinter(indent=4)

import boto3

client = boto3.client('iam')

if len(sys.argv) < 2:
	print "Tell us which access key we are looking for"
	sys.exit()

TARGET_ACCESS_KEY = sys.argv[1];

userlist = client.list_users();
users = userlist['Users']
#pp.pprint(users)

def find_key():
	for user in users:
		#print 'user dict: '
		#pp.pprint(user)
		print "checking: " +  user['UserName'] + ' ...'
		paginator = client.get_paginator('list_access_keys')
		for response in paginator.paginate(UserName=user['UserName']):
			#pp.pprint(response)
			keys = response['AccessKeyMetadata']
			#pp.pprint(keys)
			for key in keys:
				#print "     ---" + key['AccessKeyId']
				if key['AccessKeyId'] == TARGET_ACCESS_KEY:
					print "Access key " + TARGET_ACCESS_KEY + " belongs to " + user['UserName']
					return True
	return False




		#for key_result in iam.get_all_access_keys(user['user_name'])['list_access_keys_response']['list_access_keys_result']['access_key_metadata']:
		#	aws_access_key = key_result['access_key_id']
		#	if aws_access_key == TARGET_ACCESS_KEY:
		#		print 'Target key belongs to:'
		#		print 'user : ' + user['user_name']
		#		return True
#	return False

if not find_key():
	print 'Did not find access key (' + TARGET_ACCESS_KEY + ') in ' + str(len(users)) + ' IAM users.'
