#!/usr/bin/env bash


mkdir -p profile 
mkdir -p profile/nodedef
mkdir -p profile/nls
mkdir -p profile/editor

#needed for Polisy operation
#sudo pkg install py38-pillow
# only needed for PRi operation
#sudo apt-get install libxml2-dev libxslt-dev python-dev

pip3 install -r requirements_cloud.txt --user