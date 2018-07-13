#!/usr/bin/python

#this script finds all your duplicate files across multiple buckets, but you need to have read access to all buckets

import boto3
import botocore
import random
import time
import psycopg2

def main():
	dbuser = 'awsgypsy'
	dbpass = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(10))
	stackinfo = createcloudformation(dbuser,dbpass)
    	db_conn = psycopg2.connect( "dbname='awsgypsy_s3_dups_tmp_db' user='awsgypsy' host='" + stackinfo[0] + "'  password='" + dbpass + "'")
    	cursor = db_conn.cursor() # create a psycopg2 cursor that can execute queries
    	cursor.execute("""CREATE TABLE s3objects (account text, bucket text, path text, filename text, isdir boolean, md5sum text, size text);""")
	db_conn.commit()
	walk_buckets('default',db_conn) #TODO: walk orgs
	#TODO: put the delete in once we have reports
	#deletecloudformation(stackinfo[0])

#This function walks through all the buckets in your account and finds all the objects pulling out identifying information
def walk_buckets(account,db_conn):
	#s3 = boto3.resource('s3')
	s3_conn = boto3.client(service_name='s3')
	for bucket in s3_conn.list_buckets()['Buckets']:
	    bucketname = bucket['Name']
	    print("Checking Bucket: " + bucketname)
	    #for obj in bucket.objects.all():
	    objects = []
	    try: 
		objects = s3_conn.list_objects(Bucket=bucketname)['Contents'] #this fails on empty buckets, so we have to use the try
	    except:
    		print( bucketname + ' was empty')
	    for obj in objects:
		md5sum = obj['ETag']
		pathparts = obj['Key'].split('/')
		filename = pathparts.pop()
		path = "/"+"/".join(pathparts)
		sqlcmd ="INSERT INTO s3objects (account, bucket, path , filename , isdir , md5sum , size ) VALUES ('" + "','".join( [ account, bucketname, path.encode('ascii', 'ignore'), filename.encode('ascii', 'ignore'), "False", md5sum, str(obj['Size']) ] ) + "')"
		print(sqlcmd)
		cursor.execute(str(sqlcmd))
		db_conn.commit()


def createcloudformation(dbuser,dbpass):
	with open('cloudformation-db-s3-finddups.cf', 'r') as mytemplate:
    		formation_template=mytemplate.read()
	cf_client = boto3.resource('cloudformation')
	stackname = 'awsgypsy-s3-dupfinder-tmp-' + str(int(time.time()))
	#TODO: take the password out of the tags for the db, it's only there for dev purposes right now
	response = cf_client.create_stack(
	    StackName=stackname,
	    TemplateBody=formation_template,
	    Parameters=[
		{
		    'ParameterKey': 'dbuser',
		    'ParameterValue': dbuser
		},
		{
		    'ParameterKey': 'dbpass',
		    'ParameterValue': dbpass
		}

	    ],
	    Tags=[ { 'Key': 'Name', 'Value': 'awsgypsy-s3-dup-temp-db-cf' }, ]
	)
	print "Creating stack " + stackname + " ...this may take a while (7 to 10 minutes) because it's creating a database..."
	stackstatus = 'creating'
	while stackstatus != 'CREATE_COMPLETE':
		time.sleep(60)
		stackstatus = cf_client.meta.client.describe_stacks(StackName=stackname)['Stacks'][0]['StackStatus']
		print stackstatus + "..."
	print cf_client.meta.client.describe_stacks(StackName=stackname)['Stacks'][0]['Outputs']
	dbhost = cf_client.meta.client.describe_stacks(StackName=stackname)['Stacks'][0]['Outputs'][0]['OutputValue']
	#print "dbhost:" + dbhost
	print "Stack Created"
	#print response
	return [ stackname, dbhost ]


def deletecloudformation(mystack):
	cf_client = boto3.resource('cloudformation')
	response = cf_client.meta.client.delete_stack( StackName=mystack )
	print "deleting stack " + mystack

main()
