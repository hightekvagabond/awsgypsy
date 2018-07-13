#!/usr/bin/python


import boto3
from botocore.exceptions import ClientError #required for try catch on the assume role
import os
import glob 
import importlib
import shutil
import json
import datetime

table_headers = {}

def main():
	#first lets add our reports to the script
	myglobpattern = os.path.dirname(os.path.realpath(__file__)) + '/reports/*/*.py'
	print(myglobpattern)
	for file in glob.glob(myglobpattern):
		print(file)
		report_list.append(file.split('/')[-1].split('.')[0])
		#importlib.import_module




	orgclient = boto3.client('organizations')
	orgobj = orgclient.list_accounts()
	orglist = orgobj['Accounts']
	#TODO: deal with NextToken
	orgs = []
	for orgacct in orglist:
		#print("----------------------")
		#print(orgacct)
		orgs.append(orgacct['Id'])

	stsclient = boto3.client('sts')

	print("parents acct: " + boto3.client('sts').get_caller_identity().get('Account'))
	#TODO: deal with the parent account too... for now we are only going to run reports on children accounts
	for orgid in orgs:
		print("------" + orgid + "--------")
		try:
			#switchrole
			#Docs:  https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-api.html
			assumedRoleObject = stsclient.assume_role( RoleArn='arn:aws:iam::' + orgid + ':role/OrganizationAccountAccessRole', RoleSessionName='awsgypsy' + orgid)
			print(assumedRoleObject['AssumedRoleUser']['AssumedRoleId'])
			credentials = assumedRoleObject['Credentials']
			reportfiles = {}
			run_all_reports(orgid,credentials)



		except ClientError as e:
			print("Unable to assume role to account " + orgid + " : " + str(e))

	secreportfile = open(reportsdir + "security_report.html", "w")
	for reportfile in report_list:
		filename = reportsdir + reportfile + ".tmp"
		secreportfile.write("<BR/>" + reportfile + ":<TABLE Border=1><TR><TH>" + "</TH><TH>".join(table_headers[reportfile]) + "</TH></TR>")
		with open (filename, "r") as myfile:
			secreportfile.write(str(myfile.readlines()))
		myfile.close()
		secreportfile.write("</TABLE>")
	secreportfile.close()







def run_all_reports(orgid,credentials):
	mystsclient = boto3.client('sts', aws_access_key_id = credentials['AccessKeyId'], aws_secret_access_key = credentials['SecretAccessKey'], aws_session_token = credentials['SessionToken'] ) 
	print ("run all reports for " + mystsclient.get_caller_identity().get('Account'))
	for report in report_list:
		myreportfile = open(reportsdir + report + ".tmp", "a")
		globals()[report](orgid,credentials,myreportfile)
		myreportfile.close()

	




table_headers['unused_and_outdated_iam_credentials'] = ['Account','UserName','AccessKey','Created','Last Used','Age','Staleness','Action']
def unused_and_outdated_iam_credentials(orgid,credentials,myreportfile):
	print("running unused_and_outdated_iam_credentials from function")
	iamclient = boto3.client('iam',aws_access_key_id = credentials['AccessKeyId'], aws_secret_access_key = credentials['SecretAccessKey'], aws_session_token = credentials['SessionToken'] ) 
	users = iamclient.list_users()
	#print(users)
	for user in users['Users']:
		#print(user['UserName'])
		accesskeys = iamclient.list_access_keys(UserName=user['UserName'])
		#{u'AccessKeyMetadata': [{u'UserName': 'nyakovenko', u'Status': 'Active', u'CreateDate': datetime.datetime(2018, 2, 15, 22, 49, 58, tzinfo=tzutc()), u'AccessKeyId': 'AKIAJVA476NNR3KKQSZQ'}], 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': '0972ff7e-74ee-11e8-983b-b1104e53fdfd', 'HTTPHeaders': {'x-amzn-requestid': '0972ff7e-74ee-11e8-983b-b1104e53fdfd', 'date': 'Thu, 21 Jun 2018 00:57:14 GMT', 'content-length': '558', 'content-type': 'text/xml'}}, u'IsTruncated': False}
		for key in accesskeys['AccessKeyMetadata']:
			lastused = iamclient.get_access_key_last_used( AccessKeyId=key['AccessKeyId'])
			#print(lastused)
			#{u'UserName': 'sowmiyag', u'AccessKeyLastUsed': {u'Region': 'us-west-1', u'ServiceName': 's3', u'LastUsedDate': datetime.datetime(2018, 6, 20, 16, 19, tzinfo=tzutc())}, 'ResponseMetadata': {'RetryAttempts': 0, 'HTTPStatusCode': 200, 'RequestId': 'c85a5934-74ef-11e8-91bd-89bda2d952a7', 'HTTPHeaders': {'x-amzn-requestid': 'c85a5934-74ef-11e8-91bd-89bda2d952a7', 'date': 'Thu, 21 Jun 2018 01:09:43 GMT', 'content-length': '491', 'content-type': 'text/xml'}}}
			#print(lastused['AccessKeyLastUsed'])
			#{u'Region': 'us-west-1', u'ServiceName': 'ec2', u'LastUsedDate': datetime.datetime(2018, 6, 20, 19, 12, tzinfo=tzutc())}
			#{u'Region': 'N/A', u'ServiceName': 'N/A'}
			usedwhen = ''
			stale = ''
			keyage = datetime.datetime.now(key['CreateDate'].tzinfo) - key['CreateDate']
			if lastused['AccessKeyLastUsed']['ServiceName'] == 'N/A':
				usedwhen = 'Never'
				stale = keyage
			else:
				usedwhen = lastused['AccessKeyLastUsed']['LastUsedDate']
				stale = datetime.datetime.now(lastused['AccessKeyLastUsed']['LastUsedDate'].tzinfo) - lastused['AccessKeyLastUsed']['LastUsedDate']

			action = 'N/A'
			if stale.days>90:
				action = 'remove'
				
			#print(orgid + ":" + user['UserName'] + ":" + key['AccessKeyId'] + ":" + str(key['CreateDate']) + ":" + str(usedwhen))
			myreportfile.write("<TR><TD>" + "</TD><TD>".join([orgid,user['UserName'],key['AccessKeyId'],str(key['CreateDate']),str(usedwhen),str(keyage.days),str(stale.days),action]) + "</TD></TR>")
			
table_headers['volume_unattached_or_unencrypted'] = ["Account","Volume ID","State","Encryption","Action"]
def volume_unattached_or_unencrypted(orgid,credentials,myreportfile):
	#https://cloud.netapp.com/blog/automate-ebs-volumes-cost-efficiency
	print("running fvolume_unattached_or_unencryptedrom function")
	ec2res = boto3.resource('ec2',aws_access_key_id = credentials['AccessKeyId'], aws_secret_access_key = credentials['SecretAccessKey'], aws_session_token = credentials['SessionToken'] ) 
	#print(ec2res.volumes.all())
	for vol in ec2res.volumes.all():
		#print("found volume: " + str(vol))
		volinfo = ec2res.Volume(str(vol))
		#print(volinfo)
		#once we have the volume id:  https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#volume
		action = "N/A"
		if vol.state == "available":
			action = "SnapShot and Remove"
		vid = str(vol.id)
		#print(volinfo.describe_attribute(vid))
		myreportfile.write("<TR><TD>" + "</TD><TD>".join([orgid,vid,str(vol.state),"It's Not Plugged in yet",action])  + "</TD></TR>")
		
	





reportsdir = "/tmp/awsgypsy_reports/"
if os.path.isdir(reportsdir) == True:
	shutil.rmtree(reportsdir)
os.mkdir(reportsdir)
report_list = []
main()


#TODO: age of keys and volumes
 
