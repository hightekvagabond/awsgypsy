#!/usr/bin/python


import sys

import boto3    
ec2client = boto3.client('ec2')





from array import array
conn = array('i')
i = 1
# Retrieves all regions/endpoints that work with EC2
regions =  ec2client.describe_regions()
for region in regions['Regions']:
	regionname = region["RegionName"]
	#based on this: https://www.slsmk.com/how-to-use-python-boto3-to-list-instances-in-amazon-aws/
#	ec2client.setup_default_session(region_name=region["RegionName"])
	boto3.Session(region_name=region["RegionName"])
	conn = boto3.client('ec2',region_name=region["RegionName"]) #need to connect to each region individually
	response = conn.describe_instances() #http://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.describe_instances
	#response = conn.describe_instances()
	for reservation in response["Reservations"]:
	    for instance in reservation["Instances"]:
		print regionname,":",instance["Placement"]["AvailabilityZone"],instance["InstanceId"],instance["State"]["Name"]

