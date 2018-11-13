#!/usr/bin/python3

# this script is for regenerating all the artifacts for awsgypsy and putting them to git to make future installs easier
#

import os, re
from git import Repo

#get the root dir of awsgypsy
awsgypsy_dir = re.sub("ops$", "", os.path.dirname(os.path.realpath(__file__)))
os.chdir(awsgypsy_dir)

# rorepo is a Repo instance pointing to the git-python repository.
# For all you know, the first argument to Repo is a path to the repository
# you want to work with
repo = Repo(self.rorepo.working_tree_dir)
assert not repo.bare




# Set the directory you want to start from
for dirName, subdirList, fileList in os.walk(awsgypsy_dir):
    print('Found directory: %s' % dirName)
    for fname in fileList:
        print('\t%s' % fname)


#os.system('virtualenv -p python3 ' + setupdir)
#os.system('pip install requests -t ' + setupdir)
