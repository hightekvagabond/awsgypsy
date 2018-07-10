#!/bin/bash

GITMAJOR=`git --version | awk -F' ' '{print $3}' | awk -F'.' '{print $1}'`
GITMINOR=`git --version | awk -F' ' '{print $3}' | awk -F'.' '{print $2}'`
if [[ ( "$GITMAJOR" < 2 ) || ( "$GITMAJOR" > 1 && "$GITMINOR" < 13 ) ]] ; then
	echo "You need git version 2.13 or higher"
	exit 0
fi
