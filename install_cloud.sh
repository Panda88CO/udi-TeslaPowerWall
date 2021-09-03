#!/usr/bin/env bash


mkdir -p profile 
mkdir -p profile/nodedef
mkdir -p profile/nls
mkdir -p profile/editor

#needed for Polisy operation
#sudo pkg install py38-pillow
# only needed for PRi operation

pip install --upgrade pip --user

apt-get -y install libxml2-dev libxslt-dev python-dev

pip3 install --upgrade pip --user
pip install -r git+https://github.com/jrester/tesla_powerwall.git --user
#pip3 install -r tesla_powerwall --user
pip3 install -r git+https://github.com/maraujop/requests-oauth2.git --user
pip3 install -r pgc_interface --user 

pip3 install -r svglib --user
pip3 install -r reportlab --user
pip3 install -r requests --user

#pip3 install -r requirements_cloud.txt --user