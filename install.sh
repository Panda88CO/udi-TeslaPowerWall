#!/usr/bin/env bash


mkdir -p profile 
mkdir -p profile/nodedef
mkdir -p profile/nls
mkdir -p profile/editor

#needed for Polisy operation
sudo pkg install py38-pillow
# only needed for PRi operation
sudo apt-get install libxml2-dev libxslt-dev python-dev

pip install -U pip
pip3 install -U pip3

#pip install -U pip
pip3 install -r tesla_powerwall --user
pip3 install -r requests_oauth2 --user
pip3 install -r pgc_interface --user

pip3 install -r svglib --user
pip3 install -r reportlab --user
pip3 install -r requests --user

#pip install -r requirements.txt --user