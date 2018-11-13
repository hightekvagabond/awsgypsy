#!/usr/bin/python3

import boto3, sys, getopt, calendar, time, json, zipfile, os, shutil
from botocore.client import ClientError
from shutil import copyfile


awsgypsy_dir='./'
CONFIG = dict()
CONFIG['default_cloudformation_parts'] = []

default_install_dir=awsgypsy_dir + 'default_install_files/'
for part_file in os.listdir(default_install_dir):
    if part_file.endswith(".part_cf"):
        CONFIG['default_cloudformation_parts'].append(default_install_dir + part_file)


default_cf = default_install_dir + 'default_install.cf'
templatebody=""
with open(default_cf, 'r') as myfile:
    line = myfile.readline()
    while line:
        if '##insert_parts_here##' in line:
            for item in CONFIG['default_cloudformation_parts']:
                with open(item, 'r') as thispart:
                    templatebody = templatebody + str(thispart.read())
                    thispart.close()
        else:
            templatebody = templatebody + line

        line = myfile.readline()

#    templatebody = myfile.read()




print(templatebody)
