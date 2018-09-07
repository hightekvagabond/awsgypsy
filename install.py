#!/usr/bin/python

import boto3, sys, getopt, calendar, time, json
from botocore.client import ClientError

def main():
	CONFIG = getprefs()
        session = boto3.session.Session(profile_name=CONFIG["profile"])
	s3 = session.client("s3")

	default_cf = 'default_install.cf'
	with open(default_cf, 'r') as myfile:
		templatebody = myfile.read()

	#create parameters
	params = []
	configswewant = ['databucket']
	for k in configswewant:
		item = dict()
		item['ParameterKey'] = k
		item['ParameterValue'] = CONFIG[k]
		params.append(item)

	stackinfo = boto3.client('cloudformation').create_stack(
		StackName='awsgypsy-' + str(CONFIG['account']) + '-' + str(calendar.timegm(time.gmtime())),
		TemplateBody=templatebody,
    		Parameters=params,
		Capabilities=[ 'CAPABILITY_IAM' ]
		)	

	#print json.dumps(CONFIG)
	print stackinfo
	
	s3.put_object(Body=json.dumps(CONFIG), Bucket=CONFIG['databucket'], Key=CONFIG['account'] + '/CONFIG.json')


	#TODO: query the stack until it's complete and you can pull the region from the output then put the region in the path


	#s3.put_object(Body=json.dumps(stackinfo), Bucket=CONFIG['databucket'], Key=CONFIG['account'] + '/stackinfo.json')

	
	
	





def getprefs():
	CONFIG = dict()
	default_profile  = 'default'
	options, remainder = getopt.getopt(sys.argv[1:], 'a:p:', ['account=', 
                                                         'profile=',
                                                         ])
	account_from_cli = ""
	for opt, arg in options:
	    if opt in ('-a', '--account'):
	        account_from_cli = arg
	    elif opt in ('-p', '--profile'):
        	default_profile = arg

	print "\n\nThis is the installation script for awsgypsy, to use it you must have admin access connected to your awscli profile for the account you wish to install into.\n\n"
	CONFIG["account"] = raw_input("What is the aws account number for the account you are installing into? [" + account_from_cli + "] ") or account_from_cli
	if CONFIG["account"] == "":
		print "Please provide a choice account to install into"
		sys.exit()
	print "installing into account: " + CONFIG["account"]
	CONFIG["profile"] = raw_input("Which awscli credentials profile do you wish to use to? [" + default_profile  + "]  ") or default_profile


        session = boto3.session.Session(profile_name=CONFIG["profile"])

	#check if the user has admin privs
	actions = blocked(session,actions=[ 
		"ec2:DescribeInstances", 
		"iam:ListUsers", 
		"iam:ListAccessKeys", 
		"iam:DeleteAccessKey", 
		"iam:ListGroupsForUser", 
		"iam:RemoveUserFromGroup", 
		"iam:DeleteUser" ])
	if actions:
		print("Your user does not have sufficient Privillages to install this package please add these: " )
		for act in actions:
			print "\t" + str(act)
		sys.exit()


	
	default_databucket = "awsgypsy-" + CONFIG["account"] + "-data"
	CONFIG["databucket"] = raw_input("S3 Data Bucket for storing policies and user data? [" + default_databucket + "] ") or default_databucket


	s3 = session.client("s3")
	if CONFIG["databucket"] == default_databucket :
		print "checking default bucket"
		CONFIG["databucket"] = namedatabucket(s3,CONFIG['databucket'], 0)

	print("bucketname: " + CONFIG["databucket"])

	if raw_input("Set up UI? [Y/n] ").lower()[:1] != "n" :
		default_ui_bucket = "awsgypsy-" + CONFIG["account"] + "-ui"
		CONFIG["uibucket"] = raw_input("S3 UI Bucket for storing policies and user data? [" + default_ui_bucket + "] ") or default_ui_bucket
		CONFIG["uibucket"] = namedatabucket(s3,CONFIG["uibucket"], 0)

	print("ui bucketname: " + CONFIG["uibucket"])

	#check to see if we have a zone that matches the ui bucket name 


	print("Which sources would you like to inherrit your policies from? Enter them in order from least important to most important with an empty answer ending the list.")

	policies = []
	policy = "https://github.com/hightekvagabond/awsgypsy/default_policy.json"
	while policy != "" :
		policies.append(policy)
		policy = raw_input("Policy url: ")

	CONFIG["parent_policies"] = policies
	print "Policies:"
	for p in CONFIG["parent_policies"] :
		print p



#	print "Because of the way awsgypsy works it needs to be installed individually into each region, we recomend you install into all regions even the ones you are not using so that it can watch for intrusions in other regions that you are not likely to notice as you do not log into those.\n\n"
	return CONFIG


# this function figures out what the name of the bucket should be and creates it
def namedatabucket (s3, name, count):
	bucketexists = False
	bucketname = name
	if count > 0:
		print "count is " + str(count)
		bucketname = bucketname + "-" + str(count)
	try:
    		s3.head_bucket(Bucket=bucketname)
		if (raw_input("The bucket " + bucketname + " already exists and you have access to it. Would you like to use the existing data bucket? [Y/n] ").lower()[:1] != "n"):
			print("Using existing bucket '" + bucketname + "' for data and configuration")
		else:
			print("Adding a count index to the bucket name and trying again....")
			bucketexists = True
	except ClientError:
    		print "The bucket does not exist or you have no access."
		try:
	    		s3.create_bucket(Bucket=bucketname) 
		except ClientError:
 	    		print("failed to create " + bucketname)
			bucketexists = True
	if bucketexists == True:
	    print "Recursion is your friend"
	    count = count + 1 #this bucket exists, give it a number
	    bucketname = namedatabucket(s3,name,count)

	return bucketname

#this function figures out if the user has the required permisions
def blocked(session, actions, resources=None, context=None):
    """test whether IAM user is able to use specified AWS action(s)

    Args:
        actions (list): AWS action(s) to verify the IAM user can use.
        resources (list): Check if action(s) can be used on resource(s). 
            If None, action(s) must be usable on all resources ("*").
        context (dict): Check if action(s) can be used with context(s). 
            If None, it is expected that no context restrictions were set.

    Returns:
        list: Actions denied by IAM due to insufficient permissions.
    """

    if not actions:
	print("there were no actions")
        return []
    actions = list(set(actions))

    if resources is None:
        resources = ["*"]

    if context is not None:
        # Convert context dict to what ContextEntries expects.
        context_temp = []
        for context_key in context:
            context_temp.append({
                'ContextKeyName': context_key,
                'ContextKeyValues': [str(val) for val in context[context_key]],
                'ContextKeyType': "string"
            })
        context = context_temp
    else:
        context = [{}]

    aws_iam_client = session.client('iam')
    current_user_arn  = session.client('sts').get_caller_identity()['Arn']

    # You'll need to create an IAM client for this
    try:
	    results = aws_iam_client.simulate_principal_policy( PolicySourceArn=current_user_arn, ActionNames=actions, ResourceArns=resources, ContextEntries=context)['EvaluationResults']
	    blocked_actions = []
	    for result in results:
	        if result['EvalDecision'] != "allowed":
	            blocked_actions.append(result['EvalActionName'])
    except ClientError as e:
	     print "Please make sure the account has admin privillages"
             print "Unexpected error: %s" % e
	     sys.exit()



    return sorted(blocked_actions)


main()
