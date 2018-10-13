#!/usr/bin/python3

import boto3, sys, getopt, calendar, time, json, zipfile, os, shutil
from botocore.client import ClientError
from shutil import copyfile


awsgypsy_dir = os.path.dirname(os.path.realpath(__file__))



def main():
    #Get required info such as account information and source for policies
    CONFIG, session = getprefs()

    #we will need a session and s3 access later
    s3 = session.client("s3")

    #put the setup lambda in s3 for the cloudformation to use
    setupdir = awsgypsy_dir  + '/setup/'
    if not os.path.exists(setupdir):
            os.makedirs(setupdir)
    #virtualenv_cmd='virtualenv -p python3 ' + setupdir + '; source ' + setupdir + '; pip3 install requests -t ' + setupdir
    os.system('virtualenv -p python3 ' + setupdir)
    os.system('pip install requests -t ' + setupdir)
    copyfile(awsgypsy_dir + '/default_install_files/copyui.py', setupdir + 'copyui.py' )
    ZipUtilities().addMasterFolderToZip('copyui.zip', setupdir)
    CONFIG['setupkey'] =  CONFIG['account'] + '/copyui.zip'
    s3client = session.client('s3')
    s3client.upload_file('copyui.zip','awsgypsy-830488934692-data',CONFIG['setupkey'])
    os.remove(awsgypsy_dir + "/copyui.zip")
    shutil.rmtree( setupdir )

    #create parameters, this is all about putting the config information into a format the cloudformation can read
    params = []
    configswewant = ['databucket','account','uibucket','setupkey','githubbranch']
    for k in configswewant:
            item = dict()
            item['ParameterKey'] = k
            if type(CONFIG[k]) is  list :
                    item['ParameterValue'] = (' '.join(CONFIG[k]))
            else :
                    item['ParameterValue'] = CONFIG[k]
            params.append(item)


    #create the initial cloudformation
    default_cf = awsgypsy_dir + '/default_install_files/default_install.cf'
    with open(default_cf, 'r') as myfile:
            templatebody = myfile.read()
    cf_client = session.client('cloudformation')
    mystackname = 'awsgypsy-' + str(CONFIG['account']) + '-' + str(calendar.timegm(time.gmtime()))
    stackinfo = cf_client.create_stack(
    StackName=mystackname,
    TemplateBody=templatebody,
    Parameters=params,
        Capabilities=[ 'CAPABILITY_IAM' ]
        )
    CONFIG['stack_creation_info'] = stackinfo
    CONFIG['stackname'] = mystackname

    mystackstatus = ''
    while mystackstatus != "CREATE_COMPLETE" :
            time.sleep(15)
            stackdesc  = cf_client.describe_stacks( StackName=mystackname)
            mystackstatus = stackdesc['Stacks'][0]['StackStatus']
            if mystackstatus == "ROLLBACK_COMPLETE" :
                    print("Something went horribly wrong, check your cloudformation events")
                    sys.exit()
            print("Waiting for stack to complete.... current status: " + mystackstatus)

    print("Stack Is created!!!")
    print("Outputs:")
    for item in stackdesc['Stacks'][0]['Outputs']:
            print("   " + item['OutputKey']+ ":" +  item['OutputValue'])
            CONFIG[item['OutputKey']] = item['OutputValue']


    lambda_client = session.client("lambda")
    setup_lambda_desc = lambda_client.get_function( FunctionName=CONFIG['SetupFunctionARN'])
    setup_lambda_resp = lambda_client.invoke( FunctionName=setup_lambda_desc['Configuration']['FunctionName'])
    s3.put_object(Body=json.dumps(CONFIG), Bucket=CONFIG['databucket'], Key=CONFIG['setupkey'])
    print(setup_lambda_resp)
    with open(os.getenv('HOME') + '/.aws/awsgypsy/last_setup_stack', 'w') as fp:
        json.dump(CONFIG, fp, indent=4, sort_keys=True)

    #now, run the setup function
    setup_function_name=CONFIG["SetupFunctionARN"].split(":")[-1]
    lambda_response = session.client('lambda').invoke( FunctionName=setup_function_name,  Payload='{"files":"' + ",".join(os.listdir(awsgypsy_dir + "/ui/"))  + '", "setupindex":"setup_index.html"}' )
    print(lambda_response['Payload'].read().decode("UTF8") )



def getprefs():
    CONFIG = dict()
    blankkeys = ['account','databucket','uibucket','skip_prompts']
    for i in range(len(blankkeys)):
        CONFIG[blankkeys[i]] = ''

    #fill in defaults if they haven't been set
    CONFIG['profile'] = 'default'
    CONFIG['githubbranch'] = 'master'

    #this section is set up just to make development of the install.py easier and faster
    default_config = json.loads(open(os.getenv('HOME') + '/.aws/awsgypsy/setup_defaults').read())
    for key in default_config:
        CONFIG[key] = default_config[key]

    
    #pull the account and profile from command line
    options, remainder = getopt.getopt(sys.argv[1:], 'a:p:r:', ['account=', 'profile=','region=' ])
    account_from_cli = ""
    quiet=False
    for opt, arg in options:
        if opt in ('-a', '--account'):
            CONFIG['account'] = arg
        elif opt in ('-p', '--profile'):
            CONFIG['profile'] = arg
        elif opt in ('-p', '--region'):
            CONFIG['region'] = arg



    #verify or get the account number
    if CONFIG['skip_prompts'] != 'y':
        print("\n\nThis is the installation script for awsgypsy, to use it you must have admin access connected to your awscli profile for the account you wish to install into.\n\n")
        CONFIG["account"] = raw_input("What is the aws account number for the account you are installing into? [" + CONFIG['account'] + "] ") or CONFIG['account']
    if CONFIG["account"] == "":
            print("Please provide a choice account to install into")
            sys.exit()

    #verify or get the default region
    if CONFIG['skip_prompts'] != 'y':
        CONFIG["region"] = raw_input("What region are you installing into? [" + CONFIG['region'] + "] ") or CONFIG['region']

    #TODO validate region based on boto query

    #verify or get the profile used from aws credentials
    if CONFIG['skip_prompts'] != 'y':
        CONFIG["profile"] = raw_input("Which awscli credentials profile do you wish to use to? [" + CONFIG['profile']  + "]  ") or CONFIG['profile']

    #create an aws session for the blocked function to use to make sure the user has perms they need
    session = boto3.session.Session(profile_name=CONFIG["profile"], region_name=CONFIG["region"])

    #if we have a preference set to delete the old stack this part does that --this only comes from the preference file not from human input, it's for dev
    if CONFIG['delete_old'] == 'y':
        print("--------------delete the old one---------------")
        last_stack = json.loads(open(os.getenv('HOME') + '/.aws/awsgypsy/last_setup_stack').read())
        response = session.client('cloudformation').delete_stack( StackName=last_stack['stackname'])
        for bucketname in [last_stack['uibucket'],last_stack['databucket']]:
            delbucket = session.resource('s3').Bucket(bucketname)
            for key in delbucket.objects.all():
                key.delete()
            delbucket.delete()

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
                    print("\t" + str(act))
            sys.exit()

    
    CONFIG['databucket']  = "awsgypsy-" + CONFIG["account"] + "-data"
    default_databucket = CONFIG['databucket']
    if CONFIG['skip_prompts'] != 'y':
        CONFIG["databucket"] = raw_input("S3 Data Bucket for storing policies and user data? [" + CONFIG['databucket'] + "] ") or CONFIG['databucket']


    s3 = session.client("s3")
    if CONFIG["databucket"] == default_databucket :
            print( "checking default bucket")
            CONFIG["databucket"] = namedatabucket(s3,CONFIG['databucket'], 0, CONFIG)

    print("bucketname: " + CONFIG["databucket"])

    if CONFIG['skip_prompts'] != 'y':
        CONFIG['setup_ui'] = raw_input("Set up UI? [Y/n] ")

    if CONFIG['setup_ui'].lower()[:1] != "n" :
                CONFIG['uibucket']  = "awsgypsy-" + CONFIG["account"] + "-ui"
                if CONFIG['skip_prompts'] != 'y':
                    CONFIG["uibucket"] = raw_input("S3 UI Bucket for storing policies and user data? [" + CONFIG['uibucket'] + "] ") or CONFIG['uibucket']
                CONFIG["uibucket"] = namedatabucket(s3,CONFIG["uibucket"], 0, CONFIG)
                response = s3.put_bucket_policy( Bucket=CONFIG['uibucket'], Policy=open(awsgypsy_dir + "/default_install_files/ui_bucket_policy").read().replace('[[mybucketname]]', CONFIG['uibucket']))
                # Create the configuration for the website
                website_configuration = { 'ErrorDocument': {'Key': 'error.html'}, 'IndexDocument': {'Suffix': 'index.html'}, }
                # Set the new policy on the selected bucket
                s3.put_bucket_website( Bucket=CONFIG['uibucket'], WebsiteConfiguration=website_configuration)

    print("ui bucketname: " + CONFIG["uibucket"])

    #check to see if we have a zone that matches the ui bucket name 


    if CONFIG['skip_prompts'] != 'y':
        print("Which sources would you like to inherrit your policies from? Enter them in order from least important to most important with an empty answer ending the list.")

    policies = []
    policy = "https://github.com/hightekvagabond/awsgypsy/default_policy.json"
    while policy != "" :
            policies.append(policy)
            if CONFIG['skip_prompts'] != 'y':
                policy = raw_input("Policy url: ")
            else:
                policy = ""

    CONFIG["parent_policies"] = policies
    print( "Policies:")
    for p in CONFIG["parent_policies"] :
            print(p)





#	print "Because of the way awsgypsy works it needs to be installed individually into each region, we recomend you install into all regions even the ones you are not using so that it can watch for intrusions in other regions that you are not likely to notice as you do not log into those.\n\n"
    return CONFIG, session






# this function figures out what the name of the bucket should be and creates it
def namedatabucket (s3, name, count, CONFIG):
    bucketexists = False
    bucketname = name
    if count > 0:
            print("count is " + str(count))
            bucketname = bucketname + "-" + str(count)
    try:
            s3.head_bucket(Bucket=bucketname)
            if CONFIG['skip_prompts'] == 'y':
                print("Using existing bucket '" + bucketname + "' for data and configuration")
            else:
                if (raw_input("The bucket " + bucketname + " already exists and you have access to it. Would you like to use the existing data bucket? [Y/n] ").lower()[:1] != "n"):
                    print("Using existing bucket '" + bucketname + "' for data and configuration")
                else:
                        print("Adding a count index to the bucket name and trying again....")
                        bucketexists = True
    except ClientError:
            print("The bucket does not exist or you have no access.")
            try:
                    s3.create_bucket(Bucket=bucketname, ACL='authenticated-read', CreateBucketConfiguration={ 'LocationConstraint': CONFIG["region"] } ) 
            except ClientError:
                    print("failed to create " + bucketname)
                    bucketexists = True
    if bucketexists == True:
        print("Recursion is your friend")
        count = count + 1 #this bucket exists, give it a number
        bucketname = namedatabucket(s3,name,count,CONFIG)

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
         print("Please make sure the account has admin privillages")
         print("Unexpected error: %s" % e)
         sys.exit()

    return sorted(blocked_actions)

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

class ZipUtilities:
    #This function jumps into a folder and starts the process of adding it's contents to the zip file
    def addMasterFolderToZip(self, filename, folder):
            zip_file = zipfile.ZipFile(filename, 'w')
            olddir=os.getcwd()
            print("Building Zip file inside " + folder)
            os.chdir(folder)
            self.addFolderToZip(zip_file, "./")
            os.chdir(olddir)
            zip_file.close()

    #recursive function to traverse directories for adding to a zip
    def addFolderToZip(self, zip_file, folder): 
            for file in os.listdir(folder):
                    full_path = os.path.join(folder, file)
                    #print "full path is " + full_path
                    if os.path.isfile(full_path):
                            #print 'File added: ' + str(full_path)
                            zip_file.write(full_path)
                    elif os.path.isdir(full_path):
                            #print 'Entering folder: ' + str(full_path)
                            self.addFolderToZip(zip_file, full_path)




main()
